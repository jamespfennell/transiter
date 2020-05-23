from alembic import context

from transiter.db import dbconnection, models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

target_metadata = models.Base.metadata


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = dbconnection.create_engine()

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
