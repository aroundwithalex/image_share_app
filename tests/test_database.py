"""
Tests various classes and methods in database.py
"""

import pytest

from sqlalchemy import inspect
from sqlalchemy.orm import Session
from sqlalchemy import select

from image_share.database import PostgresHandler, SQLiteHandler, ImageShareDB

from image_share.models import Users, Posts, Follows


class TestPostgresHandler:
    """
    Tests methods in the PostgresHandler class.
    """

    @pytest.fixture()
    def handler(self):
        """
        Instantiates the PostgresHandler object.
        """

        params = {
            "username": "test_user",
            "password": "password",
            "host": "db_host",
            "dbname": "db_name",
        }

        return PostgresHandler(**params)

    def test_has_valid_params(self, handler):
        """
        Checks the parameters to ensure they are valid.
        """

        assert handler.has_valid_params() is True

    def test_make_connection_string(self, handler):
        """
        Checks to see whether a connection string is correctly
        created.
        """

        expected = "postgresql+pyscopg2://test_user:password@db_host/db_name"

        assert handler.make_connection_string() == expected


class TestSQLiteHandler:

    @pytest.fixture()
    def handler(self):
        """
        Instantiates the SQLiteHandler object
        """

        return SQLiteHandler(memory=True)

    def test_had_valid_params(self, handler):
        """
        Checks that the parameters are valid.
        """

        assert handler.has_valid_params() is True

    def test_make_connection_string(self, handler):
        """
        Checks to see whether the connection string was created
        properly.
        """

        expected = "sqlite://"

        assert handler.make_connection_string() == expected


class TestImageShareDB:

    @pytest.fixture()
    def db(self):
        """
        Instantiates the ImageShareDB object.
        """

        return ImageShareDB("sqlite", memory=True)

    def test_connect(self, db):
        """
        Tests connecting to a test SQLite database.
        """

        with db.session() as session:
            assert isinstance(session, Session)

    def test_has_tables(self, db):
        """
        Tests to see whether the database contains
        tables when none have been created yet.
        """

        assert db.has_tables is False

    def test_has_tables_after_created(self, db):
        """
        Tests to see whether database tables have
        been created after they should have been.
        """

        db.create_tables()

        assert db.has_tables is True

    def test_create_tables(self, db):
        """
        Tests that the tables are created in the database.
        """

        db.create_tables()

        inspector = inspect(db.engine)

        assert len(inspector.get_table_names()) > 1

    def test_validate_params(self, db):
        """
        Tests validating parameters against a database
        table to ensure that an exception is raised if
        attempting to insert invalid parameters into the
        database.
        """

        with pytest.raises(ValueError):
            db.validate_params(["Hello"], {"Users": 1})

    def test_populate(self, db):
        """
        Tests populating the database adds objects into the
        correct tables.
        """

        db.create_tables()

        db.populate()

        user = Users.get(db, user_id=1)

        assert user.user_id == 1

        follows = Follows.is_following(db, follower=1, follows=2)

        assert follows is True
