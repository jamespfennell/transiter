from setuptools import setup, find_packages

setup(
    name="Transiter",
    version="0.1dev",
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
