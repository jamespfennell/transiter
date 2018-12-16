from setuptools import setup, find_packages

setup(
    name='Transiter',
    version='0.1dev',
    packages=find_packages(),
    license='MIT',
    install_requires=[
        'apscheduler',
        'decorator',
        'flask',
        'gtfs-realtime-bindings',
        'psycopg2-binary',
        'pyyaml',
        'pytz',
        'requests',
        'rpyc',
        'sqlalchemy'
    ]
)
