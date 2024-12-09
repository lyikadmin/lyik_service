import httpx
import jwt
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)

# Custom Exceptions
class TokenNotFound(Exception): pass
class LicenseNotFound(Exception): pass
class InvalidToken(Exception): pass
class InvalidLicense(Exception): pass

class LicenseManager():
    def __init__(self, licensing_endpoint, license_key):
        self.LICENSING_ENDPOINT = licensing_endpoint
        self.LICENSE_KEY = license_key
    
    async def verify(self):
        """
        Verifies the license and raises exceptions if there are issues.
        """
        try:
            # Fetch the JWT token
            _jwt = await self.fetch()

            # Validate the token using a public key fetched via kid
            # Decode the payload and verify the license validity
            _payload = await self._get_payload(_jwt)

            # Check license validity (invalid, valid)
            valid_from = _payload["license_data"]["valid_from"]
            valid_to = _payload["license_data"]["valid_to"]
            if  self._is_premature(valid_from) or not self._is_live(valid_to):
                raise InvalidLicense("License is invalid")

            # Store license data in memory for further use
            self.license_data = _payload["license_data"]
            message = "license verification successful"
            return True, message
        except (TokenNotFound, LicenseNotFound, InvalidLicense, InvalidToken) as e:
            return False, e
        except Exception as e:
            return False, e
            
    
    async def fetch(self):
        """
        Fetches the JWT token from the server.
        There are 3 possibolities:
            1. License Found
            2. License Not Found
            3. Coundn't fetch
        """
        async with httpx.AsyncClient() as client:
            res = await client.post(f"{self.LICENSING_ENDPOINT}/verify_license", json={"key": self.LICENSE_KEY}, headers={'Content-Type': 'application/json'})
        
        response = res.json()
        if response.get('status_code') == 200:
            return response['token']
        elif response.get('status_code') == 400:
            raise LicenseNotFound("Invalid key or License not found.")
        elif response.get('status_code') == 500:
            raise TokenNotFound(f"{response.get('error')}")
    
    async def _get_payload(self, token: str):
        """
        Verifies the JWT token by checking its signature using the 'kid' and secret.
        Raises InvalidToken exception if verification fails, else returns payload
        """
        try:
            jwt_header = jwt.get_unverified_header(token)
            kid = jwt_header.get('kid')
            if not kid:
                raise InvalidToken("Token verification failed due to missing 'kid'")

            async with httpx.AsyncClient() as client:
                res = await client.post(f"{self.LICENSING_ENDPOINT}/fetch_secret", json={"kid": kid},headers={'Content-Type': 'application/json'})

            response = res.json()
            secret = response['public_key']

            return jwt.decode(token, secret, algorithms=["RS256"])

        except jwt.ExpiredSignatureError:
            raise InvalidToken("Token has expired")
        except (jwt.InvalidTokenError, Exception) as e:
            raise InvalidToken(f"Invalid token or payload could not be decoded - {str(e)}")
        
    def _is_live(self, valid_to: str) -> bool:
        """
        Checks if the license is currently valid. Allow for 7 extra days with showing a warning.
        """
        try:
            valid_to_date = datetime.strptime(valid_to, "%Y-%m-%d")
        except Exception as e:
            raise InvalidLicense(f"Date format error for valid_to: {valid_to}")
        days_remaining = (valid_to_date - datetime.now()).days
        if days_remaining < 0 and days_remaining >= -7:
            logger.warning(f"Warning!! - License expired, Server will shutdown in {7-days_remaining} days.")
        return days_remaining >= -7

    def _is_premature(self, valid_from: str) -> bool:
        """
        Checks if the license is not yet valid.
        """
        try:
            valid_from_date = datetime.strptime(valid_from, "%Y-%m-%d")
        except Exception as e:
            raise InvalidLicense(f"Date format error for valid_to: {valid_from}")
        return (valid_from_date - datetime.now()).days > 0