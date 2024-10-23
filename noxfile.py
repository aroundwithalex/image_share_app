"""
A noxfile that lints, builds and test this Python
package.
"""

from pathlib import Path

import nox


@nox.session
def lint(session):
    """
    Lints the source code using pre-commit. Refer to
    .pre-commit-config.yaml to see which tools are being
    run against the source code.
    """

    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files")


@nox.session
def build(session):
    """
    Builds a Python wheel and adds to the dist directory after
    removing obselete wheels.
    """

    # Handle first time runs
    dist_path = Path(Path.cwd(), "dist")

    if not dist_path.exists():
        dist_path.mkdir()

    # Clean wheels if any already exist
    wheels = list(dist_path.iterdir())

    if len(wheels) > 0:
        for wheel in wheels:
            wheel.unlink()

    # Now we can build this wheel
    session.install("build")

    session.run("python3", "-m", "build", "--sdist")
    session.run("python3", "-m", "build", "--wheel")


@nox.session
def test(session):
    """
    Runs unit tests with pytest.
    """

    dist_path = Path(Path.cwd(), "dist")

    wheel = list(dist_path.glob("*.whl"))

    # If more than one wheel exists, raise an error
    if len(wheel) > 1:
        raise ValueError(f"{len(wheel)} wheels found. Expected 1.")

    session.install(wheel[0])
    session.install("coverage")
    session.install("pytest")

    session.run("coverage", "run", "-m", "pytest", "-v")
    session.run("coverage", "report")
