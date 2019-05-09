from setuptools import setup, find_packages
import re

with open("transiter/metadata.py") as f:
    pattern = 'VERSION = "(?P<h>[0-9.]+)"'
    match = re.match(pattern, f.read())
    version = match.group("h")

setup(
    name="transiter",
    version=version,
    author="James Fennell",
    author_email="jamespfennell@gmail.com",
    description="HTTP web service for transit data",
    url="https://github.com/jamespfennell/transiter",
    packages=find_packages(),
    license="MIT",
    entry_points={"console_scripts": ["transiterclt = transiter.clt:transiter_clt"]},
    install_requires=[
        "apscheduler",
        "click",
        "decorator",
        "flask",
        "gtfs-realtime-bindings",
        "psycopg2-binary",
        "pytimeparse",
        "pytz",
        "requests",
        "rpyc",
        "sqlalchemy",
        "toml",
    ],
)
