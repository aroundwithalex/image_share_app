"""
Defines and creates models of the database.

Typical Usage:
>>> from image_share.models import create_models
>>> create_models(engine)
"""

from typing import Optional
from datetime import datetime

from sqlalchemy import String, SmallInteger, DateTime, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql.functions import now


def sanitise_get_args(supported_keys, **kwargs):
    """
    Sanitises arguments sent to select statements by only
    allowing supported keys to be queried.
    """

    return {a: b for a, b in kwargs.items() if a in supported_keys}


class Tables(DeclarativeBase):
    """
    Base class for models to inherit from.
    """


class Users(Tables):
    """
    Table of Users for the ImageShare App
    """

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)

    # Hash with argon2 or bcrypt
    password_hash: Mapped[str] = mapped_column(String(43), nullable=False)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # TODO: Set a default avatar if none provided
    avatar: Mapped[Optional[str]] = mapped_column(String(100))

    is_age_majority: Mapped[bool] = mapped_column(default=False)
    bio: Mapped[Optional[str]] = mapped_column(String(200))

    # Optional additonal login methods
    mobile: Mapped[Optional[int]] = mapped_column(SmallInteger())
    email: Mapped[Optional[str]] = mapped_column(String(320))

    city: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(56), nullable=False)

    date_created: Mapped[datetime] = mapped_column(default=now())
    date_updated: Mapped[Optional[datetime]] = mapped_column(onupdate=now())

    @classmethod
    def create(cls, db, **kwargs):
        """
        Creates a new User instance with associated data points.
        """

        with db.session() as session:
            new_user = cls(**kwargs)

            session.add(new_user)
            session.commit()

    @classmethod
    def get(cls, db, **kwargs):

        supported_keys = ["post_id", "user_id", "caption", "url", "timestamp"]

        sanitised_kwargs = sanitise_get_args(supported_keys, **kwargs)

        with db.session() as session:
            result = session.query(cls).filter_by(**sanitised_kwargs)

        return result.first()


class Posts(Tables):
    """
    Table of Posts for the ImageShare app
    """

    __tablename__ = "posts"

    post_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    caption: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(32767), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(default=now())
    date_created: Mapped[datetime] = mapped_column(default=now())
    date_updated: Mapped[Optional[datetime]] = mapped_column(onupdate=now())

    @classmethod
    def create(cls, db, **kwargs):
        """
        Creates a post within the database.
        """

        with db.session() as session:
            new_post = cls(**kwargs)

            session.add(new_post)
            session.commit()

    @classmethod
    def get(cls, db, **kwargs):
        """
        Retrieves a post from the database.
        """

        supported_keys = ["caption", "url", "timestamp"]

        sanitised_kwargs = sanitise_get_args(supported_keys, **kwargs)

        with db.session() as session:
            result = session.query(cls).filter_by(**sanitised_kwargs)

        return result.first()


class Follows(Tables):
    """
    Table of which user follows another user.
    """

    __tablename__ = "follows"

    follows_id: Mapped[int] = mapped_column(primary_key=True)
    follower: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    follows: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    date_followed: Mapped[datetime] = mapped_column(default=now())
    is_active: Mapped[bool] = mapped_column(default=True)
    date_unfollowed: Mapped[Optional[datetime]]

    @classmethod
    def follow(cls, db, **kwargs):
        """
        Enables one user to follow another.
        """

        if kwargs.get("is_active", None) and kwargs["is_active"] is False:
            raise ValueError("Cannot unfollow with follow().")

        with db.session() as session:
            new_follower = cls(**kwargs)

            session.add(new_follower)
            session.commit()

    @classmethod
    def unfollow(cls, db, **kwargs):
        """
        Enables a user to unfollow another user.
        """

        with db.session() as session:
            stmt = select(cls).where(
                cls.follower == kwargs["follower"], cls.follows == kwargs["follows"]
            )

            follower = session.execute(stmt).fetchone()[0]

            follower.is_active = False
            follower.date_unfollowed = datetime.now()

            session.commit()

    @classmethod
    def is_following(cls, db, **kwargs):
        """
        Checks to see whether one user is following another.
        """

        supported_keys = ["follower", "follows"]

        sanitised_kwargs = sanitise_get_args(supported_keys, **kwargs)

        with db.session() as session:
            result = session.query(cls).filter_by(**sanitised_kwargs).first()

        return False if result is None else result.is_active


class FollowedBy(Tables):
    """
    Table of which users follow another user.
    """

    __tablename__ = "followed_by"

    followed_by_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        SmallInteger(), ForeignKey("users.user_id"), nullable=False
    )
    followed_by: Mapped[int] = mapped_column(
        SmallInteger(), ForeignKey("users.user_id"), nullable=False
    )
    date_followed: Mapped[datetime] = mapped_column(default=now())
    is_active: Mapped[bool] = mapped_column(default=True)
    date_unfollowed: Mapped[Optional[datetime]]


class LikedPosts(Tables):
    """
    Table of posts linked by a user.
    """

    __tablename__ = "liked_posts"

    liked_post_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        SmallInteger(), ForeignKey("users.user_id"), nullable=False
    )
    post_id: Mapped[int] = mapped_column(
        SmallInteger(), ForeignKey("users.user_id"), nullable=False
    )
    date_liked: Mapped[datetime] = mapped_column(default=now())
    still_liked: Mapped[bool] = mapped_column(default=True)
    date_unliked: Mapped[Optional[datetime]]

    @classmethod
    def like(cls, db, **kwargs):
        """
        Enables a user to like a post.

        Args:
            cls: LikedPost class instance
            db: Database instance
            kwargs: Keyword arguments
        """

        if kwargs.get("still_liked", None) and kwargs["still_liked"] is False:
            raise ValueError("Cannot unlike a post with like()")

        with db.session() as session:

            new_like = cls(**kwargs)
            session.add(new_like)
            session.commit()

    @classmethod
    def unlike(cls, db, **kwargs):
        """
        Enables a user to unlike a post.

        Args:
            cls: LikedPost class instance
            db: Database instance
            kwargs: Keyword arguments
        """

        with db.session() as session:
            stmt = select(cls).where(
                cls.user_id == kwargs["user_id"], cls.post_id == kwargs["post_id"]
            )

            liked_post = session.execute(stmt).fetchone()[0]

            liked_post.still_liked = False
            liked_post.date_unliked = datetime.now()

            session.commit()

    @classmethod
    def is_liked(cls, db, **kwargs):
        """
        Shows whether a post is liked by a user.

        Args:
            cls: LikedPost class instance
            db: Database instance
            kwargs: Keyword arguments
        """

        supported_keys = ["user_id", "post_id"]

        sanitised_kwargs = sanitise_get_args(supported_keys, **kwargs)

        with db.session() as session:
            result = session.query(cls).filter_by(**sanitised_kwargs).first()

        return False if result is None else result.still_liked


class AgeOfMajority(Tables):
    """
    Reference table containing the age of majority
    in various countries.
    """

    __tablename__ = "age_of_majority"

    majority_id: Mapped[int] = mapped_column(primary_key=True)
