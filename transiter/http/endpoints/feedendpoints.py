from flask import Blueprint

from transiter.http.httpmanager import (
    http_endpoint,
    link_target,
    HttpMethod,
    HttpStatus,
    is_sync_request,
)
from transiter.http.permissions import requires_permissions, PermissionsLevel
from transiter.services import feedservice, links

feed_endpoints = Blueprint(__name__, __name__)


@http_endpoint(feed_endpoints, "")
@link_target(links.FeedsInSystemIndexLink)
@requires_permissions(PermissionsLevel.ADMIN_READ)
def list_all_in_system(system_id):
    """List all feeds for a specific system."""
    return feedservice.list_all_in_system(system_id)


@http_endpoint(feed_endpoints, "/<feed_id>")
@link_target(links.FeedEntityLink)
@requires_permissions(PermissionsLevel.ADMIN_READ)
def get_in_system_by_id(system_id, feed_id):
    """Retrieve a specific feed."""
    return feedservice.get_in_system_by_id(system_id, feed_id)


@http_endpoint(feed_endpoints, "/<feed_id>", method=HttpMethod.POST)
@requires_permissions(PermissionsLevel.ALL)
def create_feed_update(system_id, feed_id):
    feed_update_pk = feedservice.create_and_execute_feed_update(
        system_id, feed_id, execute_async=not is_sync_request()
    )
    return (
        feedservice.get_update_in_feed_by_pk(system_id, feed_id, feed_update_pk),
        HttpStatus.CREATED,
    )


@http_endpoint(feed_endpoints, "/<feed_id>/flush", method=HttpMethod.POST)
@requires_permissions(PermissionsLevel.ALL)
def create_feed_update_flush(system_id, feed_id):
    feed_update_pk = feedservice.create_and_execute_feed_flush(
        system_id, feed_id, execute_async=not is_sync_request()
    )
    return (
        feedservice.get_update_in_feed_by_pk(system_id, feed_id, feed_update_pk),
        HttpStatus.CREATED,
    )


@http_endpoint(feed_endpoints, "/<feed_id>/updates")
@link_target(links.FeedEntityUpdatesLink)
@requires_permissions(PermissionsLevel.ADMIN_READ)
def list_updates_in_feed(system_id, feed_id):
    """List recent feed updates."""
    return feedservice.list_updates_in_feed(system_id, feed_id)
