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

from image_share.api import app, get_db, check_environment

from image_share.auth import ImageShareAuth
from image_share.database import ImageShareDB
from image_share.models import Users


@pytest.mark.anyio
async def test_db_fails():
    """
    Ensures that db() fails if run in a directory
    without a .env file.
    """

    current_path = getcwd()

    with TemporaryDirectory() as tempdir:
        chdir(tempdir)
        with pytest.raises(HTTPException):
            database = await anext(get_db())

    chdir(current_path)


@pytest.mark.anyio
async def test_db():
    """
    Ensures that db() returns a database object.
    """

    current_path = getcwd()

    with TemporaryDirectory() as tempdir:
        chdir(tempdir)

        path = Path(".env")
        contents = "db_type=sqlite\nmemory=True"
        path.write_text(contents, newline="\n")

        database = await anext(get_db())

        assert isinstance(database, ImageShareDB)

    chdir(current_path)


@pytest.mark.anyio
async def test_check_enviroment():
    """
    Tests the check_environment() method to ensure that database
    tables are created if they don't already exist.
    """

    current_path = getcwd()
    with TemporaryDirectory() as tempdir:
        chdir(tempdir)

        path = Path(".env")
        contents = "db_type=sqlite\nmemory=True"
        path.write_text(contents, newline="\n")

        database = await anext(get_db())

        result = await check_environment(database)

        assert result.has_tables is True

    chdir(current_path)


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
