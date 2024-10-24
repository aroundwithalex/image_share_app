"""
Contains classes and methods for interacting
with the image_share database.

Typical Usage:
>>> from image_share.database import ImageShareDB
>>> db = ImageShareDB(db_type="postgres")
>>> db.create_tables()
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager

from image_share.models import Tables, Users, Posts, Follows

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from sqlalchemy import select


from image_share.models import Users


class DatabaseHandler(ABC):
    """
    Abstract base class for handling multiple
    database types.
    """

    def __init__(self, **kwargs):
        """
        Constructor that takes a series of connection parameters
        and assigns to an instance variable.
        """

        self.params = kwargs

    @property
    @abstractmethod
    def has_valid_params(self):
        """
        Checks to ensure that the parameters for a database
        connection are valid.
        """
        pass

    @abstractmethod
    def make_connection_string(self):
        """
        Generates a connection string for the specified database
        that can be used with SQLAlchemy.
        """
        pass


class PostgresHandler(DatabaseHandler):
    """
    Handles connections to a Postgres database.
    """

    def has_valid_params(self):
        """
        Ensures that a username, password, host and
        database name have been provided for the database.
        """

        required_keys = ["username", "password", "host", "dbname"]

        return all(x in self.params.keys() for x in required_keys)

    def make_connection_string(self):
        """
        Makes a connection string for SQLAlchemy to connect
        to a Postgres database.
        """

        username = self.params["username"]
        password = self.params["password"]
        host = self.params["host"]
        dbname = self.params["dbname"]

        return f"postgresql+pyscopg2://{username}:{password}@{host}/{dbname}"


class SQLiteHandler(DatabaseHandler):
    """
    Handles connections to a SQLite database.
    """

    def has_valid_params(self):
        """
        Ensures that the parameters passed are valid. Can include
        a username, password and host or just :memory:.
        """

        required_keys = ["path", "memory"]
        return any(x in self.params.keys() for x in required_keys)

    def make_connection_string(self):
        """
        Makes a connection string for a SQLite database.
        """

        if self.params.get("memory", None):
            return "sqlite://"

        path = self.params["path"]

        return f"sqlite+pysqlite:///{path}"


HANDLERS = {"postgres": PostgresHandler, "sqlite": SQLiteHandler}


class ImageShareDB:
    """
    Connects to the ImageShare database and interacts
    with it by creating tables and getting data from it.
    """

    def __init__(self, db_type: str, **kwargs):
        """
        Checks the parameters for the given database type
        and creates a connection string for it.
        """

        if db_type not in HANDLERS.keys():
            raise ValueError(f"{db_type} not supported.")

        handler = HANDLERS[db_type](**kwargs)

        if not handler.has_valid_params():
            # TODO: Use sets to determine which params are missing.
            raise ValueError(f"Connection parameters are invalid.")

        self.endpoint = handler.make_connection_string()

        self.engine = create_engine(self.endpoint)

    @contextmanager
    def session(self):
        """
        Connects to the database and returns the database session.
        """

        session = Session(self.engine)

        try:
            yield session
        finally:
            session.close()

    @property
    def has_tables(self):
        """
        Checks to see whether the database contains tables
        or not.
        """

        return len(inspect(self.engine).get_table_names()) == 6

    def create_tables(self):
        """
        Creates all models within the database.
        """

        Tables.metadata.create_all(self.engine)

    def validate_params(self, valid_keys, params):
        """
        Validates parameters that are submitted as ones to
        query the database with.

        Args:
            valid_keys: Valid query keys
            params: Submitted Parameters
        """

        has_invalid_keys = any(x not in valid_keys for x in params.keys())

        if has_invalid_keys:
            invalid_keys = set(valid_keys) - set(params)
            raise ValueError(f"{valid_keys} has invalid keys: {invalid_keys}")

    def populate(self):
        """
        Populates the database with test data when running locally.
        """

        test_user = {
            "username": "some_user",
            "password": "password",
            "first_name": "First",
            "last_name": "Last",
            "city": "Hackerville",
            "country": "Someplace",
        }

        Users.create(self, **test_user)

        test_user_2 = {
            "username": "some_user2",
            "password": "another_password",
            "first_name": "Alpha",
            "last_name": "Omega",
            "city": "Guido City",
            "country": "Pythonland",
        }

        Users.create(self, **test_user_2)

        Follows.follow(self, follower=1, follows=2)
