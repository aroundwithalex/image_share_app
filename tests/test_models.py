"""
Tests to ensure that the models have been created
correctly.
"""

import pytest

from image_share.database import ImageShareDB
from image_share.models import Users, Posts, Follows, sanitise_get_args, LikedPosts


@pytest.fixture(scope="session")
def db():
    """
    Creates a database connection and creates
    relevant tables.
    """

    db = ImageShareDB("sqlite", memory=True)

    db.create_tables()

    return db


def test_sanitise_get_args():
    """
    Tests sanitising arguments sent to a select
    request.
    """

    supported_keys = ["Hello", "User"]
    test_params = {"Goodbye": "World", "User": 1}

    sanitised_kwargs = sanitise_get_args(supported_keys, **test_params)

    assert sanitised_kwargs == {"User": 1}


class TestUsersTable:
    """
    Tests to check the integrity of the Users table.
    """

    expected_columns = [
        "user_id",
        "username",
        "password_hash",
        "first_name",
        "last_name",
        "avatar",
        "is_age_majority",
        "bio",
        "mobile",
        "email",
        "city",
        "country",
        "date_created",
        "date_updated",
    ]

    def test_create_get(self, db):
        """
        Tests the create method to ensure a new user is created
        in the database.
        """

        fields = {
            "username": "some_user",
            "password": "password",
            "first_name": "First",
            "last_name": "Last",
            "city": "Hackerville",
            "country": "Someplace",
        }

        user = Users()

        user.create(db, **fields)

        result = user.get(db, username="some_user")

        assert result.username == "some_user"

    def test_verify_password(self, db):
        """
        Test verifying a password.
        """

        fields = {
            "username": "some_user",
            "password": "password",
            "first_name": "First",
            "last_name": "Last",
            "city": "Hackerville",
            "country": "Someplace",
        }

        user = Users()

        user.create(db, **fields)

        result = user.verify_password(db, user_id=1, password="password")

        assert result is True

    def test_authenticate_user(self, db):
        """
        Tests authenticating a user against the database.
        """

        fields = {
            "username": "some_user",
            "password": "password",
            "first_name": "First",
            "last_name": "Last",
            "city": "Hackerville",
            "country": "Someplace",
        }

        user = Users()

        user.create(db, **fields)

        result = user.authenticate_user(db, user_id=1, password="password")

        assert isinstance(result, Users)

    def test_has_expected_columns(self, db):
        """
        Ensures that the Users table has the expected
        column names.
        """

        fields = {
            "username": "some_user",
            "password": "password",
            "first_name": "First",
            "last_name": "Last",
            "city": "Hackerville",
            "country": "Someplace",
        }

        Users.create(db, **fields)

        user = Users.get(db, username="some_user")

        found_fields = tuple(x for x in user.__dict__.keys() if not x.startswith("_"))

        diff = set(self.expected_columns) - set(found_fields)
        assert len(diff) == 0


class TestPostsTable:
    """
    Tests the Posts table for integrity.
    """

    expected_columns = [
        "post_id",
        "user_id",
        "caption",
        "url",
        "timestamp",
        "date_created",
        "date_updated",
    ]

    def test_create_get(self, db):
        """
        Tests creating and getting a post from the database.
        """

        fields = {
            "user_id": 1,
            "caption": "Some Caption",
            "url": "https://some_url.com",
        }

        Posts.create(db, **fields)

        results = Posts.get(db, user_id=1, caption="Some Caption")

        assert results.caption == "Some Caption"

    def test_get_posts_by_followers(self, db):
        """
        Tests fetching posts by followers.
        """

        user_fields = {
            "username": "some_user1",
            "password": "password",
            "first_name": "First",
            "last_name": "Last",
            "city": "Hackerville",
            "country": "Someplace",
        }

        Users.create(db, **user_fields)

        user2_fields = {
            "username": "some_user2",
            "password": "password",
            "first_name": "First",
            "last_name": "Last",
            "city": "Hackerville",
            "country": "Someplace",
        }

        Users.create(db, **user_fields)

        Follows.follow(db, follower=2, follows=1)

        post_fields = {
            "user_id": 2,
            "caption": "Some Caption",
            "url": "https://some_url.com",
        }

        Posts.create(db, **post_fields)

        post = Posts.get_posts_by_followers(db, user_id=1, limit=10, skip=0)

        assert post[0].caption == "Some Caption"

    def test_get_all_posts(self, db):
        """
        Tests getting all posts and ordering by number of likes.
        """

        user_fields = {
            "username": "some_user1",
            "password": "password",
            "first_name": "First",
            "last_name": "Last",
            "city": "Hackerville",
            "country": "Someplace",
        }

        Users.create(db, **user_fields)

        post_fields = {
            "user_id": 1,
            "caption": "Some Caption",
            "url": "https://some_url.com",
        }

        Posts.create(db, **post_fields)

        LikedPosts.like(db, user_id=1, post_id=1)

        post = Posts.get_all_posts(db, limit=10, skip=0)

        assert post[0][0].caption == "Some Caption"
        assert post[0][1] == 1

    def test_has_expected_columns(self, db):
        """
        Ensures that the Posts table has the expected
        columns.
        """

        fields = {
            "user_id": 1,
            "caption": "Some Caption",
            "url": "https://some_url.com",
        }

        Posts.create(db, **fields)

        results = Posts.get(db, user_id=1, caption="Some Caption")

        found_fields = tuple(
            x for x in results.__dict__.keys() if not x.startswith("_")
        )

        diff = set(self.expected_columns) - set(found_fields)
        assert len(diff) == 0


class TestFollowsTable:
    """
    Tests the Follows table for integrity.
    """

    expected_columns = [
        "follows_id",
        "follower",
        "followed_by",
        "date_followed",
        "is_active",
        "date_unfollowed",
    ]

    user_fields = {
        "username": "some_user",
        "password": "password",
        "first_name": "First",
        "last_name": "Last",
        "city": "Hackerville",
        "country": "Someplace",
    }

    user2_fields = {
        "username": "some_user2",
        "password": "password",
        "first_name": "First",
        "last_name": "Last",
        "city": "Hackerville",
        "country": "Someplace",
    }

    def test_follow_check_following(self, db):
        """
        Checks whether one user can follow another and ensures
        that that relationship is correctly identifed by the database.
        """

        Users.create(db, **self.user_fields)

        Users.create(db, **self.user2_fields)

        Follows.follow(db, follower=1, follows=2)

        assert Follows.is_following(db, follower=1, follows=2) is True

    def test_unfollow_check_following(self, db):
        """
        Checks to see whether one user can unfollow another successfully.
        """

        Users.create(db, **self.user_fields)

        Users.create(db, **self.user2_fields)

        Follows.follow(db, follower=1, follows=2)
        Follows.unfollow(db, follower=1, follows=2)

        result = Follows.is_following(db, follower=1, follows=2)
        assert result is False

    def test_mutual_followers(self, db):
        """
        Tests finding mutual followers.
        """

        Users.create(db, **self.user_fields)

        Users.create(db, **self.user2_fields)

        user3_fields = {
            "username": "some_user3",
            "password": "password",
            "first_name": "First",
            "last_name": "Last",
            "city": "Hackerville",
            "country": "Someplace",
        }

        Users.create(db, **user3_fields)

        Follows.follow(db, follower=3, follows=1)
        Follows.follow(db, follower=3, follows=2)

        result = Follows.mutual_followers(db, user1_id=1, user2_id=2)

        assert isinstance(result[0], Users)

    def test_suggest_followers(self, db):
        """
        Tests suggesting followers.
        """

        Users.create(db, **self.user_fields)

        Users.create(db, **self.user2_fields)

        user3_fields = {
            "username": "some_user3",
            "password": "password",
            "first_name": "First",
            "last_name": "Last",
            "city": "Hackerville",
            "country": "Someplace",
        }

        Users.create(db, **user3_fields)

        Follows.unfollow(db, follower=3, follows=1)
        Follows.follow(db, follower=3, follows=2)

        result = Follows.suggest_followers(db, user1_id=1, user2_id=2)

        assert result[0].user_id == 3


class TestLikedPostsTable:
    """
    Unit tests for the LikedPosts table
    """

    user_fields = {
        "username": "some_user",
        "password": "password",
        "first_name": "First",
        "last_name": "Last",
        "city": "Hackerville",
        "country": "Someplace",
    }

    post_fields = {
        "user_id": 1,
        "caption": "Some Caption",
        "url": "https://some_url.com",
    }

    def test_like_is_liked(self, db):
        """
        Tests the like() and is_liked() methods.
        """

        Users.create(db, **self.user_fields)
        Posts.create(db, **self.post_fields)

        LikedPosts.like(db, user_id=1, post_id=1)

        assert LikedPosts.is_liked(db, user_id=1, post_id=1) is True

    def test_unlike_is_liked(self, db):
        """
        Tests the unlike() and is_liked_methods.
        """

        Users.create(db, **self.user_fields)
        Posts.create(db, **self.post_fields)

        LikedPosts.like(db, user_id=1, post_id=1)
        LikedPosts.unlike(db, user_id=1, post_id=1)

        assert LikedPosts.is_liked(db, user_id=1, post_id=1) is False
