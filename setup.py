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
        "apscheduler==3.6.1",
        "click==7.0",
        "decorator==4.4.1",
        "flask==1.1.1",
        "gtfs-realtime-bindings==0.0.6",
        "psycopg2-binary==2.8.4",
        "pytimeparse==1.1.8",
        "pytz==2019.3",
        "requests==2.22.0",
        "rpyc==4.1.2",
        "sqlalchemy==1.3.10",
        "strictyaml==1.0.5",
    ],
)
