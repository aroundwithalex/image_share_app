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

First, make sure that you have a tool called `uv` installed. This is a next-
generation Python tool that enables the packaging of Python projects, the
installation of dependencies within virtual environments and the syncing of
dependencies across machines. Download in a UNIX-based environment using this
command: `curl -LsSf https://astral.sh/uv/install.sh | sh` or alternatively
consult [this link](https://docs.astral.sh/uv/getting-started/installation/)
for more details.

With `uv` installed, you should be able to set up the environment by running `uv sync`. This will
install all of the dependencies in the uv lock file, which will guarantee that the same
dependencies will be installed regardless of environmental differences. If any of the dependencies
appear to be broken, find the last unbroken version and run `uv add <dependency>==<version>`.  For
instance, after this project was first submitted, there was an issue with `bcrypt` which broke the
library that used it as a backend: `passlib`. To resolve the dependency conflict in this case, it
was necessary to run `uv add bcrypt==4.0.0`, which replaced the broken version of `bcrypt` with one
that works.

To run the project locally, you will need to have a `.env` file. Typically this
will require five keys: -

```
DB_TYPE=sqlite
MEMORY=true
SECRET_KEY=<secret_key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

The application will use this to spin up an in-memory SQLite database and will
use the other fields for generating a JWT token.

Please note that you will need to create your own secret key using the OpenSSL
library. This is used for authenticating with JWT tokens. This can be done using
by running `openssl rand -hex 32`. If you have issues running that command, check
to ensure `openssl` is installed on your machine and add if missing. Alternatively,
go to [this page] (https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) on
the FastAPI documentation for more details.

To run the unit tests, run `uv run pytest -v`. This will run all of the unit tests
within an isolated environment. To run the endpoints, use `uv run fastapi dev app.py`.


# Additional areas of work

- Add machine learning models for image classification and captions
with scikit-learn.
- Finish integration of JWT tokens to protect API endpoints.
