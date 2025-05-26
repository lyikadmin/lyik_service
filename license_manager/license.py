from datetime import datetime, timedelta
import logging
import os

import httpx
import jwt
import pymongo
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Custom Exceptions
class TokenNotFound(Exception): pass
class LicenseNotFound(Exception): pass
class InvalidToken(Exception): pass
class InvalidLicense(Exception): pass

class OrgCollection(BaseModel):
    license_key: str
    organization_name: str
    license_expiry_time: datetime
    cache_expiry_time: datetime
    no_of_hits: int

class MongoDBOperations:
    def __init__(self):
        self.MONGO_CONN_URL = os.getenv("MONGO_CONN_URL")
        self.client = pymongo.MongoClient(host=self.MONGO_CONN_URL)
        self.DB_NAME = "lyikservices"
        self.ORGS_COLL = "orgs"

    def get_license_data(self, license_key: str):
        _coll = self.client[self.DB_NAME][self.ORGS_COLL]
        return _coll.find_one({"license_key": license_key})

    def update_license_cache(self, license_key: str, license_data: dict):
        _coll = self.client[self.DB_NAME][self.ORGS_COLL]
        now = datetime.now()
        expiry_time = LicenseManager.to_datetime(license_data["valid_to"])
        _coll.update_one(
            {"license_key": license_key},
            {
                "$set": {
                    "organization_name": license_data["organisation_name"],
                    "license_expiry_time": expiry_time,
                    "cache_expiry_time": now + timedelta(hours=24),
                },
                "$inc": {"no_of_hits": 1}
            },
            upsert=True
        )

    def increment_hits_and_refresh_cache(self, license_key: str):
        _coll = self.client[self.DB_NAME][self.ORGS_COLL]
        now = datetime.now()
        _coll.update_one(
            {"license_key": license_key},
            {
                "$inc": {"no_of_hits": 1},
                "$set": {"cache_expiry_time": now + timedelta(hours=24)}
            }
        )

mongo = MongoDBOperations()

class LicenseManager:
    def __init__(self, license_key):
        self.LICENSING_ENDPOINT = os.getenv("LICENSING_ENDPOINT")
        self.LICENSE_KEY = license_key

    async def verify(self):
        try:
            license_data = mongo.get_license_data(self.LICENSE_KEY)
            now = datetime.now()

            if license_data:
                cache_expiry = self.to_datetime(license_data.get("cache_expiry_time"))
                license_expiry = self.to_datetime(license_data.get("license_expiry_time"))

                if cache_expiry > now and license_expiry > now:
                    mongo.increment_hits_and_refresh_cache(self.LICENSE_KEY)
                    return True, "License verified from cache."

            _jwt = await self.fetch()
            _payload = await self._get_payload(_jwt)

            valid_from = _payload["license_data"]["valid_from"]
            valid_to = _payload["license_data"]["valid_to"]

            if self._is_premature(valid_from) or not self._is_live(valid_to):
                raise InvalidLicense("License is invalid")

            self.license_data = _payload["license_data"]
            self.organisation_name = self.license_data["organisation_name"]

            mongo.update_license_cache(self.LICENSE_KEY, self.license_data)
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
