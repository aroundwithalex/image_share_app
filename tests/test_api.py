"""
Unit tests for the various API methods
"""

from tempfile import TemporaryDirectory
from contextlib import _GeneratorContextManager
from os import chdir, getcwd
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import HTTPException
from fastapi.testclient import TestClient

from image_share.api import app, get_db, check_environment, get_current_user

from image_share.auth import ImageShareAuth
from image_share.database import ImageShareDB
from image_share.models import Users


@pytest.mark.anyio
async def test_root():
    """
    Tests the root path of the API.
    """

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200


@pytest.mark.anyio
async def test_user_id():
    """
    Tests the /user/{user_id} endpoint.
    """

    with TestClient(app) as client:
        response = client.get("/users/1")

        assert response.status_code == 200
        assert response.json()["user_id"] == 1


@pytest.mark.anyio
async def test_follow_user():
    """
    Tests the /follow/ endpoint.
    """

    with TestClient(app) as client:

        response = client.post("/follow/", json={"user_id": "3", "follows": "2"})

        assert response.status_code == 200
        assert response.json()["status"] == "success"


@pytest.mark.anyio
async def test_unfollow_user():
    """
    Tests the /unfollow/ endpoint
    """

    with TestClient(app) as client:
        client.post("/follow/", json={"user_id": "4", "follows": "2"})

        response = client.post("/unfollow/", json={"user_id": "4", "follows": "2"})

        assert response.status_code == 200
        assert response.json()["status"] == "success"


@pytest.mark.anyio
async def test_upload_image():
    """
    Tests uploading an image to /posts/upload
    """

    test_image = Path(Path.cwd(), "tests", "test_image.jpg")

    with test_image.open("rb") as image_file:
        files = {"image": image_file}
        form_data = {"caption": "Some caption", "url": "https://example.com"}

        with TestClient(app) as client:
            response = client.post("/posts/upload", files=files, data=form_data)

            assert response.status_code == 200
            assert response.json()["status"] == "success"


@pytest.mark.anyio
async def test_like_post():
    """
    Tests liking a post with the /posts/like/ endpoint. Should
    return a successful HTTP response.
    """

    with TestClient(app) as client:
        response = client.post("/posts/like/", json={"user_id": 1, "post_id": 1})
        assert response.status_code == 200
        assert response.json()["status"] == "success"


@pytest.mark.anyio
async def test_unlike_post():
    """
    Tests unliking a post with the /posts/unlike endpoint. Should
    return a successful HTTP response.
    """

    with TestClient(app) as client:
        client.post("/posts/like/", json={"user_id": 1, "post_id": 1})
        response = client.post("/posts/unlike", json={"user_id": 1, "post_id": 1})
        assert response.status_code == 200
        assert response.json()["status"] == "success"


@pytest.mark.anyio
async def test_posts_by_followers():
    """
    Tests whether posts made by followers are returned correctly from
    the posts/{user_id}/by-followers endpoint.
    """

    with TestClient(app) as client:
        response = client.get("/posts/by-followers?user_id=1&limit=10&skip=0")

        assert response.status_code == 200
        assert isinstance(response.json()["posts"], list)


@pytest.mark.anyio
async def test_get_all_posts():
    """
    Tests whether all posts are correctly returned from the /posts/all
    endpoint.
    """

    with TestClient(app) as client:
        response = client.get("/posts/all?limit=10&skip=0")

        assert response.status_code == 200
        assert isinstance(response.json()["posts"], list)


@pytest.mark.anyio
async def test_mutual_followers():
    """
    Tests whether two users have mutual followers.
    """

    with TestClient(app) as client:
        response = client.get("/mutual-followers?user1_id=1&user2_id=2")

        assert response.status_code == 200
        assert response.json()["num_mutual_followers"] == 0


@pytest.mark.anyio
async def test_suggest_followers():
    """
    Tests suggesting followers to a user.
    """

    with TestClient(app) as client:
        response = client.get("/suggest-followers?user1_id=1&user2_id=2")

        assert response.status_code == 200
        assert response.json()["num_suggested_followers"] == 0


@pytest.mark.anyio
async def test_generate_access_token():
    """
    Tests generating an access token.
    """

    db = ImageShareDB("sqlite", memory=True)

    db.create_tables()

    user_fields = {
        "username": "some_user",
        "password": "password",
        "first_name": "First",
        "last_name": "Last",
        "city": "Hackerville",
        "country": "Someplace",
    }

    Users.create(db, **user_fields)

    with TestClient(app) as client:

        form_data = {"username": "some_user", "password": "password"}
        response = client.post("/token", data=form_data)

        assert response.status_code == 200
        assert response.json()["access_token"].startswith("ey")
