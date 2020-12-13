"""
Helper script for running the CI job.

TODO: it would be great to not use environment variables
 as input to the script but use command line args instead.
"""
import os
import subprocess
import sys
import time

import docker

METADATA_FILE = "transiter/__metadata__.py"
METADATA_FILE_TEMPLATE = """
# NOTE: the following were set by the CI process
__version__ = "{version}"
__build_number__ = {build_number}
__build_timestamp__ = {build_timestamp}
__build_href__ = "{build_href}"
__git_commit_hash__ = "{git_commit_hash}"
"""


def calculate_base_version():
    """
    The base version is the version reported in __metadata__.py, less any dev flag.
    """
    metadata = {}
    with open(METADATA_FILE) as f:
        exec(f.read(), metadata)
    version = metadata["__version__"]
    dev_postfix = version.rfind(".dev")
    if dev_postfix >= 0:
        version = version[:dev_postfix]
    return version


def calculate_version():
    """
    If not running on CI, the version is the same as the base version.

    Otherwise, if this is a tagged release, then the version is the tag which is
    required to be equal to the version in __metadata__.py.

    If this is not a tagged release the version is the base version with an
    additional ".dev#" postfix where # is the build ID.
    """
    version = calculate_base_version()

    build_number = os.environ.get("BUILD_ID")
    print("The build ID is", build_number)
    if build_number is not None:
        if not is_release():
            version += ".dev{}".format(build_number)

    return version


def set_version(new_version):
    """
    Set the version in __metadata__.py.
    """
    new_content = METADATA_FILE_TEMPLATE.format(
        version=new_version,
        build_number=os.environ.get("BUILD_NUMBER"),
        build_timestamp=int(time.time()),
        build_href=os.environ.get("CI_WEB_URL"),
        git_commit_hash=os.environ.get("GIT_COMMIT_HASH"),
    )
    print("Updating __metadata__.py by appending:")
    print(new_content)
    with open(METADATA_FILE, "a") as f:
        f.write(new_content)


def is_release():
    """
    True if this is a build on a release tag.
    """
    git_ref = os.environ.get("GIT_REF")
    if git_ref is None:
        print("This is not a release because the git_ref env variable is not set")
        return False
    else:
        print("Git ref is:", git_ref)
    if not git_ref.startswith("refs/tags"):
        print("This is not a release because the commit is not tagged")
        return False
    print("This commit is tagged")
    return git_ref == ("refs/tags/" + calculate_base_version())


def is_mainline_build():
    """
    True if this is a build on master or a release tag.
    """
    if os.environ.get("IS_PULL_REQUEST") == "false":
        print("This is not a mainline build because it is a pull request")
        return False
    else:
        print("This is NOT a pull request")
    if os.environ.get("GIT_REF") == "refs/heads/master":
        print("This is a mainline build because the branch is 'master'")
        return True
    else:
        print("This is NOT a build on 'master'")
    if is_release():
        print("This is a mainline build because it is a release")
        return True
    print("This is not a release or a mainline build")
    return False


def get_artifacts_to_push():
    """
    Using the commit message, determine which artifacts to push.

    Returns a set possibly containing "docker" and "pypi"
    """
    if not is_mainline_build():
        print("Not pushing any artifacts because this is not a mainline release")
        return set()
    if is_release():
        print("Pushing docker and pypi automatically as this is a release")
        return {"docker", "pypi"}
    message = os.environ.get("GIT_COMMIT_MESSAGE", "").splitlines()
    result = {"docker", "pypi"}
    for line in message:
        if line[:6] != "push: ":
            continue
        result = set()
        for artifact in {"docker", "pypi"}:
            if artifact in line:
                result.add(artifact)
        break
    print("Will push the following artifacts:", result)
    return result


def upload_to_py_pi():
    """
    Upload the Transiter Python package inside the CI container to PyPI.

    If this is not a build on master or a release tag, this is a no-op.
    """
    if "pypi" not in get_artifacts_to_push():
        return
    print("Uploading to PyPI")
    subprocess.run(
        [
            "docker",
            "run",
            "--env",
            "TWINE_USERNAME=" + os.environ.get("TWINE_USERNAME"),
            "--env",
            "TWINE_PASSWORD=" + os.environ.get("TWINE_PASSWORD"),
            "jamespfennell/transiter-ci:latest",
            "distribute",
        ]
    )


def upload_to_docker_hub():
    """
    Upload the Transiter Docker images to Docker Hub.

    If this is not a build on master or a release tag, this is a no-op.
    """
    if "docker" not in get_artifacts_to_push():
        return
    print("Uploading to Docker Hub")
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
        image = client.images.get("jamespfennell/transiter:latest")
        image.tag(full_image_name)
        print("Pushing image:", full_image_name)
        print(client.images.push(full_image_name))


command = sys.argv[1]

print("Transiter version:", calculate_version())
if command == "before":
    set_version(calculate_version())
elif command == "after":
    upload_to_py_pi()
    upload_to_docker_hub()
else:
    raise ValueError("Unknown command '{}'!".format(command))
