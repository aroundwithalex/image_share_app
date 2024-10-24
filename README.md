# Image Share App

This project is in fulfilment of a technical test set by Hedgehog
labs. It contains the basic structure of an image sharing app.

# Key points about the code and design

The code is designed to be as flexible as possible, adhering to SOLID
principles such as open/closed. For this reason, both the authentication
and the database files implement handlers, to enable the codebase to be
extended without having to modify existing code. The API endpoints are
built to be asychronous, to enable them to scale in a real-world context.
Both SQLAlchemy and pydantic models were used; the former to define
database tables and the latter for data validation.

# Database schema

There are multiple tables within the database to capture details about
users, followers and posts. These tables are designed to scale as the
application grows, containing more information than a basic image sharing
app needs but enough to enable it to grow. It also contains various defaults
and methods for interacting with the database.

# How to run

There are a couple of ways of running the project. The first is to
just run the test suite via `pytest -v` or `uv run pytest -v`. You'll
need to install the requirements in the uv.lock file first.

# Additional areas of work

- Add machine learning models for image classification and captions
with scikit-learn.
