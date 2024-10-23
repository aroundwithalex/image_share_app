"""
Contains the routes and the logic for the API
that returns data about users, posts, followers et al.

Typical Usage:

>>> from image_share.api import app
>>> app()
"""

from typing import Annotated
from os import environ
from contextvars import ContextVar
import logging
from pathlib import Path

from fastapi import Depends, FastAPI, File, UploadFile, HTTPException, Form
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.exc import SQLAlchemyError

from image_share.database import ImageShareDB
from image_share.models import Users, Posts, Follows, LikedPosts
from image_share.auth import ImageShareAuth

logger = logging.getLogger(__name__)


async def get_db():
    """
    Creates and returns a database object.
    """

    try:
        environ["ImageShare_Env"] = "local"
        auth = ImageShareAuth()
        credentials = auth.db_credentials()

        db_type = credentials.pop("db_type")
        db = ImageShareDB(db_type, **credentials)

        yield db

    except ValueError as val_err:
        # Probably due to issues authenticating with the
        # database.
        msg = f"Database Authentication Error: {val_err}"
        raise HTTPException(status_code=403, detail=msg)

    except SQLAlchemyError as sql_err:
        msg = f"Database Error: {sql_err}"
        raise HTTPException(status_code=500, detail=msg)


app: object = FastAPI()


@app.on_event("startup")
async def check_environment(database: object = Depends(get_db)):
    """
    Checks the environment that we're running in and does
    various things based on that. For instance, if we're
    running a local environment and the database doesn't
    exist, it will be created.
    """

    database = await anext(get_db())
    in_local_environment = environ["ImageShare_Env"] == "local"
    has_database_tables = database.has_tables

    if in_local_environment and not has_database_tables:
        database.create_tables()
        database.populate()

    app.state.db = database

    return database


@app.get("/")
async def root():
    """
    Root view of the API that returns a simple
    JSON greeting the user.
    """
    return {"Hello": "World"}


@app.post("/posts/upload")
async def upload_image(
    image: UploadFile, caption: str = Form(...), url: HttpUrl = Form(...)
):
    """
    Endpoint to enable users to submit an image along with associated
    details such as a caption and a URL.

    Args:
        image: The file uploaded by the user
        details: Caption and URL assoicated with the image
    """

    db = app.state.db

    supported_suffixes = ["jpeg", "jpg", "png", "webp"]

    if not any(image.filename.endswith(x) for x in supported_suffixes):
        raise HTTPException(status_code=403, details="Invalid file upload")

    # TODO: Change to /mnt when running on prod
    root_path = Path("/tmp", "image_share")

    if not root_path.exists():
        root_path.mkdir()

    image_path = root_path / image.filename

    try:
        with image_path.open("wb") as image_file:
            while contents := image.file.read(1024 * 1024):
                image_file.write(contents)
    except Exception:
        raise HTTPError(status_code=500, details="Image upload failed")
    finally:
        image.file.close()

    return {
        "status": "success",
        "image_name": image.filename,
        "caption": caption,
        "url": url,
    }


@app.get("/users/{user_id}")
async def get_user_details(user_id: int):
    """
    Returns data about the user.

    Args:
        user_id: ID of the user
        db: Database object
    """

    fields = {
        "username": "some_user",
        "password_hash": "password",
        "first_name": "First",
        "last_name": "Last",
        "city": "Hackerville",
        "country": "Someplace",
    }

    database = app.state.db

    database.create_tables()

    Users.create(database, **fields)

    user = Users.get(database, user_id=user_id)

    if not user:
        raise HTTPException(status_code=404, details="User not found")

    serialised_data = jsonable_encoder(user)
    return JSONResponse(content=serialised_data)


class Follower(BaseModel):
    user_id: str
    follows: int


@app.post("/follow/")
async def follow_user(follower: Follower):
    """
    Enables one user to follow another.

    Args:
        Follower object submitted as JSON
    """

    db = app.state.db

    params = {"follower": follower.user_id, "follows": follower.follows}

    if Follows.is_following(db, **params):
        raise HTTPException(status_code=403, details="Already following user")

    Follows.follow(db, **params)

    return {
        "status": "success",
        "msg": f"{follower.user_id} now following {follower.follows}",
    }


@app.post("/unfollow/")
async def unfollow_user(follower: Follower):
    """
    Enables one user to unfollow another user.

    Args:
        Follower object submitted as JSON
    """

    db = app.state.db

    params = {"follower": follower.user_id, "follows": follower.follows}

    if not Follows.is_following(db, **params):
        raise HTTPException(status_code=403, details="Not following user")

    Follows.unfollow(db, **params)

    return JSONResponse(
        {
            "status": "success",
            "msg": f"{follower.user_id} unfollowed {follower.follows}",
        }
    )


class Like(BaseModel):
    user_id: int
    post_id: int


@app.post("/posts/like/")
async def like_post(like: Like):
    """
    Enables a user to like a post.

    Args:
        Like model that contains a user_id and a post_id
    """

    db = app.state.db

    params = {"user_id": like.user_id, "post_id": like.post_id}

    if LikedPosts.is_liked(db, **params):
        raise HTTPException(status_code=403, details="Post already liked.")

    LikedPosts.like(db, **params)

    return JSONResponse(
        {"status": "success", "msg": f"{like.user_id} likes {like.post_id}"}
    )


@app.post("/posts/unlike/")
async def unlike_post(unlike: Like):
    """
    Enables a user to unlike a post.

    Args:
        user_id: ID of the user unliking the post
        post_id: ID of the post to unlike.
    """
    db = app.state.db

    params = {"user_id": unlike.user_id, "post_id": unlike.post_id}

    if not LikedPosts.is_liked(db, **params):
        raise HTTPException(status_code=403, detail="Post not currently liked")

    LikedPosts.unlike(db, **params)

    return JSONResponse(
        {
            "status": "success",
            "msg": f"{unlike.user_id} no longer likes {unlike.post_id}",
        }
    )


@app.get("/posts/{user_id}/by-followers")
async def posts_by_followers(user_id: int):
    """
    Lists posts by followers, sorted by the most
    recent.

    Args:
        user_id: ID of the user to list posts for
    """


@app.get("/posts/all")
async def all_posts():
    """
    Lists all posts, sorted by the number of likes.
    """
    pass


@app.get("/users/{user1_id}/mutual-followers/{user2_id}")
async def mutual_followers(user1_id: int, user2_id: int):
    """
    Lists mutual followers between two users.

    Args:
        user1_id: ID of profile viewer
        user2_id: ID of profile owner
    """
    pass