from setuptools import setup, find_packages

setup(
    name='Transiter',
    version='0.1dev',
    packages=find_packages(),
    license='MIT',
    entry_points={
        'console_scripts': [
            'transiter-task-server = transiter.taskserver.server:launch',
            'transiter-http-debug-server = transiter.http.flaskapp:launch',
            'transiter-rebuild-db = transiter.data.database:rebuild_db'
        ]
    },
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
