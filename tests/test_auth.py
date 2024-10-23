"""
Unit tests for the authentication.py
"""

from tempfile import TemporaryDirectory
from pathlib import Path
from os import chdir

import pytest

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

        assert local_auth.can_operate() is True

    def test_get_credentials(self, local_auth):
        """
        Ensures that LocalAuth.get_credentials returns
        a dictionary.
        """

        assert isinstance(local_auth.get_credentials(), dict)

    def test_default(self, local_auth):
        """
        Tests the default property to ensure it returns
        the expected result.
        """

        expected = {"db_type": "sqlite", "memory": True}

        assert local_auth.default() == expected


class TestImageShareAuth:
    """
    Contains unit tests for the ImageShareAuth object.
    """

    @pytest.fixture(scope="session")
    def dir_context(self):
        """
        Sets the directory context that a unit test should
        run in.
        """

        with TemporaryDirectory() as tempdir:
            chdir(tempdir)

            data = (
                "db_type=sqlite\n"
                "username=user\n"
                "password=pwd\n"
                "host=host\n"
                "dbname=name\n"
                "secret_key=123\n"
                "algorithm=some_algo\n"
                "access_token_expire_minutes=1"
            )

            path = Path(".env")
            path.write_text(data, newline="\n")

            yield path

    @pytest.fixture
    def image_share_auth(self, dir_context):
        """
        Creates the ImageShareAuth object and returns.
        """

        yield ImageShareAuth()

    def test_local_default(self, image_share_auth):
        """
        Ensures that ImageShareAuth() defaults to the local
        environment.
        """

        assert image_share_auth.environment == "local"

    def test_db_credentials(self, image_share_auth):
        """
        Ensures that the correct database credentials are loaded.
        """

        expected = {
            "db_type": "sqlite",
            "username": "user",
            "password": "pwd",
            "host": "host",
            "dbname": "name",
        }

        credentials = image_share_auth.db_credentials()

        assert credentials == expected

    def test_api_credentials(self, image_share_auth):
        """
        Tests fetching API credentials from a .env file.
        """

        expected = {
            "secret_key": "123",
            "algorithm": "some_algo",
            "access_token_expire_minutes": "1",
        }

        credentials = image_share_auth.api_credentials()

        print(expected, credentials)

        assert credentials == expected

    def test_db_credentials_default(self):
        """
        Ensures that the default values are returned if
        the .env file is missing required keys.
        """

        with TemporaryDirectory() as tempdir:

            chdir(tempdir)
            path = Path(".env")
            path.touch()

            expected = {"db_type": "sqlite", "memory": True}

            auth = ImageShareAuth()

            credentials = auth.db_credentials()

            assert credentials == expected
