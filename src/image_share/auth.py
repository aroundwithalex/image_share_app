"""
Collection of classes and modules to handle
authentication for the ImageShare app.
"""

from typing import Optional

from pathlib import Path
from abc import ABC, abstractmethod
from os import environ
from datetime import timedelta, datetime

from dotenv import dotenv_values
from passlib.context import CryptContext
import jwt


class AuthHandler(ABC):
    """
    Abstract base class for getting authentication
    details from a range of sources, including AWS
    and locally.
    """

    @abstractmethod
    def can_operate(self):
        """
        Ensures that the relevant files and connections
        exist before trying to get credentials.
        """
        pass

    @abstractmethod
    def get_credentials(self):
        """
        Gets credentials from the specified source and
        returns as a dictionary.
        """
        pass


class LocalAuth(AuthHandler):
    """
    Handles local authentication by trying to find a
    .env file in the source directory of this application.
    """

    def __init__(self):
        """
        Gets the current working directory and assigns as
        an instance variable.
        """

        self.path = Path(Path.cwd(), ".env")

    def can_operate(self):
        """
        Checks to see whether the .env file exists and
        whether it is accessible.
        """

        return self.path.exists()

    def get_credentials(self):
        """
        Fetches credentials from a .env file and returns
        in a dictionary.
        """

        return dotenv_values(str(self.path))


# TODO: Change production handler to a secret storage
# manager rather than a .env file.

HANDLERS = {"local": LocalAuth, "production": LocalAuth}


class ImageShareAuth:
    """
    Class for handling authentication for the ImageShare app.
    """

    def __init__(self):
        """
        Tries to find the environment that the application is
        running in and sets as an instance variable. Defaults
        to local if unknown.
        """

        env = environ.get("ImageShare_Env", None)

        self.environment = "local" if env is None else env

        self.handler = HANDLERS[self.environment]()

        if not self.handler.can_operate():
            raise ValueError("Unable to find credentials.")

        self.raw_credentials = self.handler.get_credentials()

    def db_credentials(self):
        """
        Fetches credentials and ensures they are properly
        formatted into a dictionary.
        """

        required_keys = ["DB_TYPE", "MEMORY"]

        has_required_keys = all(x in self.raw_credentials for x in required_keys)

        if not has_required_keys:
            raise ValueError("Missing required database keys")

        filtered_credentials = {
            a: b for a, b in self.raw_credentials.items() if a in required_keys
        }

        return {a.lower(): b for a, b in self.raw_credentials.items()}

    def api_credentials(self):
        """
        Gets API credentials for generating a JWT token.
        """

        required_keys = ["SECRET_KEY", "ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES"]

        has_required_keys = all(x in self.raw_credentials for x in required_keys)

        filtered_credentials = {
            a: b for a, b in self.raw_credentials.items() if a in required_keys
        }

        return {a.lower(): b for a, b in filtered_credentials.items()}

    @classmethod
    def get_crypt_context(cls):
        """
        Simple class method that returns the default context for
        password hashing.
        """

        return CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(self, data: dict):
        """
        Creates a JWT access token.

        Args:
            data: Data to encode
            expires: Timedelta for token expiry

        Returns:
            Encoded JWT web token
        """

        encoded_data = data.copy()

        credentials = self.api_credentials()

        expiry = credentials["access_token_expire_minutes"]

        expire = datetime.utcnow() + timedelta(minutes=int(expiry))

        encoded_data.update({"exp": expiry})

        encoded_jwt = jwt.encode(
            encoded_data, credentials["secret_key"], credentials["algorithm"]
        )

        return encoded_jwt
