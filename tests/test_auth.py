"""
Unit tests for the authentication.py
"""

from tempfile import TemporaryDirectory
from pathlib import Path
from os import chdir, getcwd

import pytest
from passlib.context import CryptContext

from image_share.auth import LocalAuth, ImageShareAuth


class TestLocalAuth:
    """
    Unit tests for the LocalAuth class.
    """

    @pytest.fixture
    def local_auth(self):
        """
        Instantisates the LocalAuth object.
        """

        with TemporaryDirectory() as tempdir:
            chdir(tempdir)

            path = Path(".env")
            path.touch()

            yield LocalAuth()

    def test_can_operate(self, local_auth):
        """
        Ensures that LocalAuth can operate because a
        .env file exists.
        """

        with TemporaryDirectory() as tempdir:
            chdir(tempdir)

            path = Path(".env")
            path.touch()

            auth = LocalAuth()
            assert auth.can_operate() is True

    def test_get_credentials(self, local_auth):
        """
        Ensures that LocalAuth.get_credentials returns
        a dictionary.
        """

        assert isinstance(local_auth.get_credentials(), dict)


class TestImageShareAuth:
    """
    Contains unit tests for the ImageShareAuth object.
    """

    @pytest.fixture(scope="class")
    def dir_context(self):
        """
        Sets the directory context that a unit test should
        run in.
        """

        current_path = getcwd()
        with TemporaryDirectory() as tempdir:
            chdir(tempdir)

            data = (
                "db_type=sqlite\n"
                "username=user\n"
                "password=pwd\n"
                "host=host\n"
                "dbname=name\n"
                "secret_key=123\n"
                "algorithm=HS256\n"
                "access_token_expire_minutes=1"
            )

            path = Path(".env")
            path.write_text(data, newline="\n")

            yield path

        chdir(current_path)

    @pytest.fixture
    def image_share_auth(self, dir_context):
        """
        Creates the ImageShareAuth object and returns.
        """

        yield ImageShareAuth()

    def test_db_credentials(self):
        """
        Ensures that the correct database credentials are loaded.
        """

        expected = {
            "db_type": "sqlite",
            "memory": "true",
            "secret_key": "123",
            "algorithm": "HS256",
            "access_token_expire_minutes": "1",
        }

        with TemporaryDirectory() as tempdir:
            chdir(tempdir)

            data = (
                "DB_TYPE=sqlite\n"
                "MEMORY=true\n"
                "SECRET_KEY=123\n"
                "ALGORITHM=HS256\n"
                "ACCESS_TOKEN_EXPIRE_MINUTES=1"
            )

            path = Path(".env")
            path.write_text(data, newline="\n")

            image_share_auth = ImageShareAuth()

            credentials = image_share_auth.db_credentials()

        assert credentials == expected

    def test_api_credentials(self):
        """
        Tests fetching API credentials from a .env file.
        """

        expected = {
            "secret_key": "123",
            "algorithm": "HS256",
            "access_token_expire_minutes": "1",
        }

        with TemporaryDirectory() as tempdir:
            chdir(tempdir)

            data = (
                "DB_TYPE=sqlite\n"
                "USERNAME=user\n"
                "PASSWORD=pwd\n"
                "HOST=host\n"
                "DB_NAME=name\n"
                "SECRET_KEY=123\n"
                "ALGORITHM=HS256\n"
                "ACCESS_TOKEN_EXPIRE_MINUTES=1"
            )

            path = Path(".env")
            path.write_text(data, newline="\n")

            image_share_auth = ImageShareAuth()

            credentials = image_share_auth.api_credentials()

            print(credentials, expected)

        assert credentials == expected

    def test_get_crypt_context(self):
        """
        Ensures that get_crypt_context correctly returns
        an CryptContext object.
        """

        assert isinstance(ImageShareAuth.get_crypt_context(), CryptContext)

    def test_create_access_token(self):
        """
        Tests create_access_token method.
        """

        with TemporaryDirectory() as tempdir:
            chdir(tempdir)

            data = (
                "DB_TYPE=sqlite\n"
                "USERNAME=user\n"
                "PASSWORD=pwd\n"
                "HOST=host\n"
                "DB_NAME=name\n"
                "SECRET_KEY=123\n"
                "ALGORITHM=HS256\n"
                "ACCESS_TOKEN_EXPIRE_MINUTES=1"
            )

            path = Path(".env")
            path.write_text(data, newline="\n")

            image_share_auth = ImageShareAuth()

            token = image_share_auth.create_access_token(data={"sub": "some_user"})

            assert token.startswith("ey") is True
