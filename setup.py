from setuptools import setup, find_packages

metadata = {}
with open("transiter/__version__.py") as f:
    exec(f.read(), metadata)
version = metadata["__version__"]

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
        "strictyaml",
    ],
)
