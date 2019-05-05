from setuptools import setup, find_packages


setup(
    name="transiter",
    version="0.1.2",
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
