from setuptools import setup, find_packages

setup(
    name="transiter",
    version="0.1.1",
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
