import datetime
import logging

from transiter import models
from transiter.data import database
from transiter.data.dams import feeddam
from transiter.general import linksutil, exceptions
from transiter.services.update import updatemanager

logger = logging.getLogger(__name__)


@database.unit_of_work
def list_all_autoupdating():
    """
    List all auto updating feeds. This method is designed for use by the task
    server
    :return:
    """
    response = []
    for feed in feeddam.list_all_autoupdating():
        response.append({
            'pk': feed.pk,
            'id': feed.id,
            'system_id': feed.system.id,
            'auto_update_period': feed.auto_updater_frequency
        })
    return response


@database.unit_of_work
def list_all_in_system(system_id):

    response = []

    for feed in feeddam.list_all_in_system(system_id):
        feed_response = feed.short_repr()
        feed_response.update({
            'href': linksutil.FeedEntityLink(feed),
        })
        response.append(feed_response)
    return response


@database.unit_of_work
def get_in_system_by_id(system_id, feed_id):

    feed = feeddam.get_in_system_by_id(system_id, feed_id)
    if feed is None:
        raise exceptions.IdNotFoundError
    response = {
        **feed.short_repr(),
        'updates': {
            'href': linksutil.FeedEntityUpdatesLink(feed)
        }
    }
    return response


@database.unit_of_work
def create_feed_update(system_id, feed_id):

    feed = feeddam.get_in_system_by_id(system_id, feed_id)
    if feed is None:
        raise exceptions.IdNotFoundError
    feed_update = models.FeedUpdate(feed)
    updatemanager.execute_feed_update(feed_update)
    return {
        **feed_update.long_repr()
    }


@database.unit_of_work
def list_updates_in_feed(system_id, feed_id):
    # TODO optimize this to only be one query? yes yes
    feed = feeddam.get_in_system_by_id(system_id, feed_id)
    if feed is None:
        raise exceptions.IdNotFoundError
    response = []
    for feed_update in feeddam.list_updates_in_feed(feed):
        response.append(feed_update.short_repr())
    return response


@database.unit_of_work
def trim_feed_updates():
    logger.info('Trimming old feed updates.')
    before_datetime = (
        datetime.datetime.now() - datetime.timedelta(minutes=60)
    ).replace(microsecond=0, second=0)
    logger.info('\n' + _build_feed_updates_report(before_datetime))
    logger.info('Deleting feed updates in DB before {}'.format(before_datetime))
    feeddam.trim_feed_updates(before_datetime)


def _build_feed_updates_report(before_datetime):
    table_row_template = '{delimiter}'.join([
        '{system_id:13}', '{feed_id:20}', '{status:10}', '{explanation:20}',
        '{count:>5}', '{avg_execution_duration:>6}'
    ])
    table_rows = [
        'Aggregated feed update report for updates in the database before {}'.format(
            before_datetime),
        '',
        'Column explanations:',
        '+ number of feed updates of this type',
        '* average execution time for feed updates of this type',
        '',
        table_row_template.format(
            delimiter=' | ',
            system_id='system_id',
            feed_id='feed_id',
            status='status',
            explanation='explanation',
            count='*',
            avg_execution_duration='+'
        )
    ]
    feed_id = None
    status = None
    for feed_update_data in feeddam.aggregate_feed_updates(before_datetime):
        if feed_update_data['feed_id'] != feed_id:
            table_rows.append(
                table_row_template.format(
                    delimiter='-+-',
                    system_id='-'*13,
                    feed_id='-'*20,
                    status='-'*10,
                    explanation='-'*20,
                    count='-'*5,
                    avg_execution_duration='-'*6
                )
            )
            feed_id = table_feed_id = feed_update_data['feed_id']
            table_system_id = feed_update_data['system_id']
        else:
            table_feed_id = ''
            table_system_id = ''

        if feed_update_data['status'] != status or table_feed_id != '':
            status = table_status = feed_update_data['status']
        else:
            table_status = ''

        table_rows.append(
            table_row_template.format(
                delimiter=' | ',
                system_id=table_system_id,
                feed_id=table_feed_id,
                status=table_status,
                explanation=feed_update_data['explanation'],
                count=feed_update_data['count'],
                avg_execution_duration='{:.2f}'.format(feed_update_data['avg_execution_duration'])
            )
        )

    return '\n'.join(table_rows)
