from datetime import datetime, timedelta
import logging
import os
import httpx
import jwt
from pydantic import BaseModel
from cachetools import TTLCache
from typing import Tuple

logger = logging.getLogger(__name__)

# Exceptions
class TokenNotFound(Exception): pass
class LicenseNotFound(Exception): pass
class InvalidToken(Exception): pass
class InvalidLicense(Exception): pass

# TTL Cache for license info: max 100 items, 24hr TTL
LICENSE_CACHE = TTLCache(maxsize=100, ttl=86400)
MESSAGE = str

class LicenseManager:
    def __init__(self, license_key):
        self.LICENSING_ENDPOINT = os.getenv("LICENSING_ENDPOINT")
        self.LICENSE_KEY = license_key

    async def verify(self) -> Tuple[bool, MESSAGE]:
        try:
            now = datetime.now()
            license_data = LICENSE_CACHE.get(self.LICENSE_KEY)

            if license_data:
                license_expiry = self.to_datetime(license_data["license_expiry_time"])
                if license_expiry > now:
                    return True, "License verified from cache."

            # Cache expired or missing; fetch fresh
            _jwt = await self.fetch()
            _payload = await self._get_payload(_jwt)

            valid_from = _payload["license_data"]["valid_from"]
            valid_to = _payload["license_data"]["valid_to"]

            if self._is_premature(valid_from) or not self._is_live(valid_to):
                raise InvalidLicense("License is invalid")

            license_data = {
                "organization_name": _payload["license_data"]["organisation_name"],
                "license_expiry_time": valid_to,
            }

            LICENSE_CACHE[self.LICENSE_KEY] = license_data
            return True, "License verified with server."

        except (TokenNotFound, LicenseNotFound, InvalidLicense, InvalidToken) as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    async def fetch(self):
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{self.LICENSING_ENDPOINT}/verify_license",
                json={"key": self.LICENSE_KEY},
                headers={"Content-Type": "application/json"},
            )
        response = res.json()
        if response.get("status_code") == 200:
            return response["token"]
        elif response.get("status_code") == 400:
            raise LicenseNotFound("Invalid key or License not found.")
        elif response.get("status_code") == 500:
            raise TokenNotFound(f"{response.get('error')}")

    async def _get_payload(self, token: str):
        try:
            jwt_header = jwt.get_unverified_header(token)
            kid = jwt_header.get('kid')
            if not kid:
                raise InvalidToken("Token verification failed due to missing 'kid'")

            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{self.LICENSING_ENDPOINT}/fetch_secret",
                    json={"kid": kid},
                    headers={'Content-Type': 'application/json'}
                )

            response = res.json()
            secret = response['public_key']
            return jwt.decode(token, secret, algorithms=["RS256"])

        except jwt.ExpiredSignatureError:
            raise InvalidToken("Token has expired")
        except (jwt.InvalidTokenError, Exception) as e:
            raise InvalidToken(f"Invalid token or payload could not be decoded - {str(e)}")

    def _is_live(self, valid_to) -> bool:
        valid_to_date = self.to_datetime(valid_to)
        days_remaining = (valid_to_date - datetime.now()).days
        if days_remaining < 0 and days_remaining >= -7:
            logger.warning(f"Warning!! - License expired, Server will shutdown in {7 - days_remaining} days.")
        return days_remaining >= -7

    def _is_premature(self, valid_from) -> bool:
        valid_from_date = self.to_datetime(valid_from)
        return (valid_from_date - datetime.now()).days > 0

    @staticmethod
    def to_datetime(value):
        if isinstance(value, datetime):
            return value
        try:
            if isinstance(value, (int, float)):
                return datetime.fromtimestamp(value)
            elif isinstance(value, str):
                try:
                    return datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    return datetime.fromisoformat(value)
        except Exception:
            raise InvalidLicense(f"Cannot parse datetime from value: {value}")
