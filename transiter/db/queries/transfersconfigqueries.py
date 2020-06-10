from sqlalchemy.orm import selectinload

from transiter.db import dbconnection, models


def list_all():
    return (
        dbconnection.get_session()
        .query(models.TransfersConfig)
        .options(selectinload(models.TransfersConfig.systems))
        .all()
    )


def get(config_id):
    return (
        dbconnection.get_session()
        .query(models.TransfersConfig)
        .filter(models.TransfersConfig.pk == config_id)
        .options(selectinload(models.TransfersConfig.systems))
        .options(selectinload(models.TransfersConfig.transfers))
        .options(
            selectinload(models.TransfersConfig.transfers, models.Transfer.from_stop)
        )
        .options(
            selectinload(models.TransfersConfig.transfers, models.Transfer.to_stop)
        )
        .one_or_none()
    )
