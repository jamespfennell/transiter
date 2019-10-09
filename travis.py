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
    git_tag = os.environ.get("TRAVIS_TAG")
    if git_tag == "":
        git_tag = None
    if travis_build_number is not None:
        if git_tag is None:
            version += ".dev{}".format(travis_build_number)
        else:
            assert git_tag == version

    return version


def is_dev_version():
    travis_build_number = os.environ.get("TRAVIS_BUILD_NUMBER")
    git_tag = os.environ.get("TRAVIS_TAG")
    if git_tag == "":
        git_tag = None
    if travis_build_number is None:
        return True
    if git_tag is None:
        return True
    return False


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


def is_mainline_build():
    if os.environ.get("TRAVIS_BUILD_NUMBER") is None:
        return False
    if os.environ.get("TRAVIS_BRANCH") != "master":
        return False
    if os.environ.get("TRAVIS_PULL_REQUEST") != "false":
        return False
    return True


def upload_to_py_pi():
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
    if not is_mainline_build():
        return
    client = docker.from_env()
    client.login(
        username=os.environ.get("DOCKER_USERNAME"),
        password=os.environ.get("DOCKER_PASSWORD"),
    )
    image_names = ["webserver", "taskserver", "postgres"]

    if is_dev_version():
        latest_prefix = "latest-dev"
    else:
        latest_prefix = "latest"
    for prefix in [latest_prefix, calculate_version()]:
        for image_name in image_names:
            full_image_name = "jamespfennell/transiter:{}-{}".format(prefix, image_name)
            image = client.images.get(
                "jamespfennell/transiter:latest-{}".format(image_name)
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
