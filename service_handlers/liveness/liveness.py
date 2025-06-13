import os
import re
import wave
from typing import List, Tuple
from geopy.geocoders import Nominatim
import av
import whisper
import logging
import difflib
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
            f"Captcha match result: {match_found}, \ntranscription: {transcribed_text}, \nkeywords: {keyword_list}"
        )
        if match_found:
            return match_found, transcribed_text
        elif not transcribed_text:
            transcribed_text = ["No audio/spoken text detected in the video"]
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
        result = model.transcribe(audio=audio_path, language="en")
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
    transcribed_text: List[str],
    keywords: List[str],
    match_score: float = 0.80,
) -> bool:
    """
    Return True if ≥ `match_score` fraction of UNIQUE keywords are present.

    Handles:
        • normal words ('hello') and case-insensitive matches
        • spoken numbers ('eight' → '8')
        • digits run together ('8187106')
        • digits split across tokens ('8187', '106')
    """
    if not keywords:
        return False

    # Canonicalise keywords and drop any '0'
    keyword_str = "".join(keywords)
    # keyword_set = {
    #     kw for k in keywords
    #     if (kw := _canonicalise(k)) != '0'
    # }

    digits = _extract_tokens(transcribed_text)
    spoken_digits = "".join(digits)

    # matched = sum(
    #     1
    #     for kw in keyword_set
    #     if kw in tokens or any(kw in run for run in digit_runs)
    # )

    m = difflib.SequenceMatcher(None, keyword_str, spoken_digits)
    # fraction = matched / len(keyword_set) if keyword_set else 0

    logger.debug(
        "Transcription match score: %.2f (%s/%s keywords)",
        m.ratio(),
        keyword_str,
        spoken_digits,
    )

    return m.ratio() >= match_score


_WORD_TO_DIGIT = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "zero": "0",
}


def _canonicalise(token: str) -> str:
    """Lower-case + map number-words → digits"""
    token_lc = token.lower()
    return _WORD_TO_DIGIT.get(token_lc, token_lc)


def _split_digits(run: str) -> list[str]:
    """
    Break a string of digits into the shortest sequence of numbers drawn from 1-10,
    skipping 0 entirely.

    Examples
    --------
    '106'      -> ['10', '6']
    '10106'    -> ['10', '10', '6']
    '807'      -> ['8', '7']       # '0' is discarded
    """
    parts: list[str] = []
    i = 0
    while i < len(run):
        # Look for '10'
        if run[i] == "1" and i + 1 < len(run) and run[i + 1] == "0":
            parts.append("10")
            i += 2
        else:
            if run[i] != "0":  # ignore lone zeros
                parts.append(run[i])
            i += 1
    return parts


def _extract_tokens(text: List[str]) -> List[str]:
    """
    Build
      • a set of canonical tokens (words + numbers 1-10);
      • a list of full digit runs (for substring checks where useful).
    """
    digits: list[str] = []

    for word in text:
        w = word.lower()

        # always add the literal word itself
        # If any non numerals are read should we consider. Right now no !
        # tokens.add(w)

        # add its numeric equivalent if it's a number-word (1-10 only)
        if w in _WORD_TO_DIGIT:
            digits.append(_WORD_TO_DIGIT[w])
            continue

        # pick out every run of digits inside the word
        for run in re.findall(r"\d+", w):
            digits.append(run)
            # tokens.add(run)            # whole run, e.g. '106'
            # tokens.update(_split_digits(run))   # e.g. '10', '6'

    return digits
