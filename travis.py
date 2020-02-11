"""
Helper script for running the Travis job.
"""
import os
import sys
import subprocess

import docker

VERSION_FILE = "transiter/__version__.py"


def calculate_base_version():
    """
    The base version is the version reported in __version__.py, less any dev flag.
    """
    metadata = {}
    with open(VERSION_FILE) as f:
        exec(f.read(), metadata)
    version = metadata["__version__"]
    dev_postfix = version.rfind(".dev")
    if dev_postfix >= 0:
        version = version[:dev_postfix]
    return version


def calculate_version():
    """
    If not running on Travis, the version is the same as the base version.

    Otherwise, if this is a tagged release, then the version is the tag which is
    required to be equal to the version in __version__.py.

    If this is not a tagged release the version is the base version with an
    additional ".dev#" postfix, where the number is the Travis job num,ber.
    """
    version = calculate_base_version()

    travis_build_number = os.environ.get("TRAVIS_BUILD_NUMBER")
    if travis_build_number is not None:
        if not is_release():
            version += ".dev{}".format(travis_build_number)

    return version


def set_version(new_version):
    """
    Set the version in __version__.py.
    """
    print("Setting version to be '{}'".format(new_version))
    with open(VERSION_FILE, "a") as f:
        f.write(
            "# The following version was set by travis.py.\n"
            '__version__ = "{}"\n'.format(new_version)
        )


def is_release():
    """
    True if this is a build on a release tag.
    """
    travis_branch = os.environ.get("TRAVIS_BRANCH")
    return (
        travis_branch is not None
        and travis_branch == os.environ.get("TRAVIS_TAG")
        and travis_branch == calculate_base_version()
    )


def is_mainline_build():
    """
    True if this is a build on master or a release tag.
    """
    return os.environ.get("TRAVIS_PULL_REQUEST") == "false" and (
        os.environ.get("TRAVIS_BRANCH") == "master" or is_release()
    )


def upload_to_py_pi():
    """
    Upload the Transiter Python package inside the CI container to PyPI.

    If this is not a build on master or a release tag, this is a no-op.
    """
    if not is_mainline_build():
        return
    subprocess.run(
        [
            "docker",
            "run",
            "--env",
            "TWINE_USERNAME=" + os.environ.get("TWINE_USERNAME"),
            "--env",
            "TWINE_PASSWORD=" + os.environ.get("TWINE_PASSWORD"),
            "jamespfennell/transiter:latest-ci",
            "distribute",
        ]
    )


def upload_to_docker_hub():
    """
    Upload the Transiter Docker images to Docker Hub.

    If this is not a build on master or a release tag, this is a no-op.
    """
    if not is_mainline_build():
        return
    client = docker.from_env()
    client.login(
        username=os.environ.get("DOCKER_USERNAME"),
        password=os.environ.get("DOCKER_PASSWORD"),
    )

    prefixes = ["latest-dev", calculate_version()]
    if is_release():
        prefixes.append("latest")
    for prefix in prefixes:
        full_image_name = "jamespfennell/transiter:{}".format(prefix)
        image = client.images.get(
            "jamespfennell/transiter:latest"
        )
        image.tag(full_image_name)
        print(client.images.push(full_image_name))


command = sys.argv[1]

if command == "before":
    set_version(calculate_version())
elif command == "after":
    upload_to_py_pi()
    upload_to_docker_hub()
    print(calculate_version())
else:
    raise ValueError("Unknown command '{}'!".format(command))
