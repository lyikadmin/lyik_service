import os
import re
import wave
from typing import List, Tuple
from geopy.geocoders import Nominatim
import av
import whisper
import logging
from models import ResponseStatusEnum, StandardResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def process_liveness(
    video_path: str, lat: float, lng: float, captcha_list: List[str]
) -> StandardResponse:
    """
    Main entry function for liveness check. Verifies:
    1. Geolocation: checks if lat/lng is in India.
    2. Captcha Keywords: extracts audio from video, transcribes, and checks if captcha keywords match.
    Returns a standardised response using StandardResponse.
    """
    try:
        # Geolocation check
        if not is_location_in_country(lat, lng):
            return StandardResponse(
                status=ResponseStatusEnum.failure.value,
                message="Geolocation check failed: location not in India.",
                result={"liveness_status": "failed"},
            )

        # File existence check
        if not os.path.exists(video_path):
            return StandardResponse(
                status=ResponseStatusEnum.failure.value,
                message=f"Video file '{video_path}' not found.",
                result={"liveness_status": "error"},
            )

        # Match captcha keywords
        match_found, transcribed_text = match_captcha_keywords(captcha_list, video_path)

        if match_found:
            return StandardResponse(
                status=ResponseStatusEnum.success.value,
                message="Verification successful: transcription matched keywords.",
                result={
                    "liveness_status": "verified",
                    "transcription": " ".join(transcribed_text),
                },
            )
        else:
            return StandardResponse(
                status=ResponseStatusEnum.failure.value,
                message="Verification failed: captcha keywords not matched. ".join(
                    transcribed_text
                ),
                result={"liveness_status": " ".join(transcribed_text)},
            )

    except Exception as e:
        logger.error(f"Error during liveness check {e}")
        return StandardResponse(
            status=ResponseStatusEnum.failure.value,
            message=f"Unexpected error during liveness check: {str(e)}",
            result={"liveness_status": "error"},
        )


def is_location_in_country(
    lat: float, lng: float, desired_country: str = "India"
) -> bool:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut
    from time import sleep

    retries = 3  # Number of retries
    timeout = 5  # Timeout duration in seconds

    geolocator = Nominatim(user_agent="geo_verifier", timeout=timeout)

    for attempt in range(retries):
        try:
            location = geolocator.reverse((lat, lng))
            if location and desired_country in location.address:
                return True
            return False
        except GeocoderTimedOut:
            print(f"Timeout occurred. Retrying... Attempt {attempt + 1} of {retries}")
            sleep(2**attempt)  # Exponential backoff: 2, 4, 8 seconds
        except Exception as e:
            raise Exception(f"Error during geolocation check: {e}")

    raise Exception("Failed to fetch geolocation data after multiple retries.")


def match_captcha_keywords(
    captcha_list: List[str], video_path: str
) -> Tuple[bool, List[str]]:
    keyword_list = [kw.lower().strip() for kw in captcha_list]

    audio_path = None
    try:
        audio_path = extract_audio_from_video(video_path)
        transcribed_text = speech_to_text(audio_path)
        match_found = match_keywords(transcribed_text, keyword_list)
        logger.debug(
            f"Captcha match result: {match_found}, transcription: {transcribed_text}, keywords: {keyword_list}"
        )
        if match_found:
            return match_found, transcribed_text
        else:
            transcribed_text = [
                f"Failed Captcha matching. Transcription: '{transcribed_text}'. Captcha: '{keyword_list}'"
            ]
            return match_found, transcribed_text
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)


def extract_audio_from_video(video_path: str) -> str:
    audio_output = "extracted_audio.wav"
    try:
        container = av.open(video_path)
        audio_stream = next((s for s in container.streams if s.type == "audio"), None)

        if not audio_stream:
            raise ValueError(f"No audio stream found in the video file '{video_path}'.")

        resampler = av.audio.resampler.AudioResampler(
            format="s16p", layout="mono", rate=44100
        )

        with wave.open(audio_output, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(44100)

            for frame in container.decode(audio_stream):
                frame.pts = None
                resampled_frames = resampler.resample(frame)
                for resampled_frame in resampled_frames:
                    wav_file.writeframes(resampled_frame.to_ndarray().tobytes())

        container.close()

        if os.path.exists(audio_output):
            file_size = os.path.getsize(audio_output)
            logger.debug(
                f"Audio file '{audio_output}' created, size: {file_size} bytes."
            )
        else:
            raise RuntimeError("Failed to create audio file.")

        return audio_output

    except Exception as e:
        raise Exception(f"Error during audio extraction: {e}")


def speech_to_text(audio_path: str, model_name="base") -> List[str]:
    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(audio=audio_path)
        text = str(result["text"]).lower()
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        words = text.strip().split()
        return words
    except Exception as e:
        raise Exception(f"Error converting speech to text: {e}")


# def match_keywords(transcribed_text: List[str], keywords: List[str]) -> bool:
#     match_score = 0.10
#     keyword_index = 0
#     for word in transcribed_text:
#         if keyword_index < len(keywords) and word == keywords[keyword_index]:
#             keyword_index += 1
#         if keyword_index == len(keywords):
#             break
#     score = keyword_index / len(keywords) if keywords else 0
#     return score >= match_score


def match_keywords(
    transcribed_text: List[str], keywords: List[str], match_score: float = 0.5
) -> bool:
    """
    Returns True if the fraction of unique keywords found in transcribed_text
    is at least match_score, else False.

    Example:
      match_keywords(
         ['sir', 'tune', 'imagine', 'body', 'further', 'plane'],
         ['cell', 'tune', 'imagine', 'border', 'fairly', 'plane'],
         match_score=0.5
      )
      -> True (because we match 3 out of 6 keywords => 0.5 => 50%)
    """
    if not keywords:
        # No keywords means there's nothing to match, so return False by default
        return False

    transcribed_set = set(transcribed_text)
    keyword_set = set(keywords)

    # Count how many unique keywords appear in transcribed_text
    matched_count = sum(1 for kw in keyword_set if kw in transcribed_set)

    # Fraction of keywords matched
    fraction_matched = matched_count / len(keyword_set)

    return fraction_matched >= match_score
