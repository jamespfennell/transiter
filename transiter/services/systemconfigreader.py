import enum

import jinja2
import pytimeparse
import pytz
import strictyaml
from strictyaml import (
    Any,
    Bool,
    EmptyList,
    EmptyDict,
    Float,
    Map,
    MapPattern,
    Optional,
    ScalarValidator,
    Seq,
    Str,
)
from strictyaml.exceptions import YAMLSerializationError

from transiter import exceptions
from transiter.db import models
from transiter.services.servicemap import conditions


class HumanReadableTimePeriod(ScalarValidator):
    """
    A validator the converts human readable time period like "10 minutes" into the
    number of seconds in the period, as determined by pytimeparse.
    """

    def validate_scalar(self, chunk):
        value = pytimeparse.parse(chunk.contents)
        if value is None:
            chunk.expecting_but_found(
                "when expecting something that could be interpreted as a time period",
                "found '{}'".format(chunk.contents),
            )
        return value

    @staticmethod
    def to_yaml(data):
        return "{} seconds".format(data)


class Timezone(ScalarValidator):
    def validate_scalar(self, chunk):
        try:
            pytz.timezone(chunk.contents)
        except pytz.exceptions.UnknownTimeZoneError:
            chunk.expecting_but_found(
                "when expecting a valid timezone specifier",
                "found '{}'".format(chunk.contents),
            )
        return chunk.contents

    @staticmethod
    def to_yaml(data):
        return data


class PyEnum(ScalarValidator):
    """
    A validator for enum.Enum types. This validator ensures that the provided string
    in the YAML file is the name of one of the enum's elements, and then casts the
    result to that enum element.
    """

    def __init__(self, enum_):
        self._enum = enum_
        assert issubclass(
            self._enum, enum.Enum
        ), "argument must be a enum.Enum or subclass thereof"

    def validate_scalar(self, chunk):
        try:
            val = self._enum[chunk.contents]
        except KeyError:
            chunk.expecting_but_found(
                "when expecting one of: {0}".format(
                    ", ".join(elem.name for elem in self._enum)
                )
            )
        else:
            return val

    def to_yaml(self, data):
        if not isinstance(data, self._enum):
            raise YAMLSerializationError(
                "Got '{0}' when  expecting one of: {1}".format(
                    data, ", ".join(str(elem) for elem in self._enum)
                )
            )
        return data.name

    def __repr__(self):
        return u"PyEnum({0})".format(repr(self._enum))


class ServiceMapConditions(Map):
    def __init__(self):
        super().__init__(
            {
                Optional(conditions.ALL_OF): self,
                Optional(conditions.ENDS_EARLIER_THAN): Float(),
                Optional(conditions.ENDS_LATER_THAN): Float(),
                Optional(conditions.NONE_OF): self,
                Optional(conditions.ONE_OF): self,
                Optional(conditions.STARTS_EARLIER_THAN): Float(),
                Optional(conditions.STARTS_LATER_THAN): Float(),
                Optional(conditions.WEEKDAY): Bool(),
                Optional(conditions.WEEKEND): Bool(),
            }
        )


# These are all constants so that reading the JSON response is less fragile
AUTO_UPDATE = "auto_update"
BUILT_IN = "built_in"
CONDITIONS = "conditions"
CUSTOM = "custom"
DIRECTION_RULES_FILES = "direction_rules_files"
ENABLED = "enabled"
FEEDS = "feeds"
HEADERS = "headers"
HTTP = "http"
NAME = "name"
OPTIONS = "options"
PREFERRED_ID = "preferred_id"
PACKAGES = "packages"
PARSER = "parser"
PERIOD = "period"
REQUIRED_FOR_INSTALL = "required_for_install"
REQUIRED_SETTINGS = "required_settings"
REQUIREMENTS = "requirements"
SERVICE_MAPS = "service_maps"
SETTINGS = "settings"
SOURCE = "source"
THRESHOLD = "threshold"
TIMEOUT = "timeout"
TIMEZONE = "timezone"
URL = "url"
USE_FOR_ROUTES_AT_STOP = "use_for_routes_at_stop"
USE_FOR_STOPS_IN_ROUTE = "use_for_stops_in_route"


default_service_map_config = {
    "all-times": {
        SOURCE: models.ServiceMapGroup.ServiceMapSource.SCHEDULE,
        THRESHOLD: 0.1,
        USE_FOR_STOPS_IN_ROUTE: True,
    },
    "weekday": {
        SOURCE: models.ServiceMapGroup.ServiceMapSource.SCHEDULE,
        THRESHOLD: 0.1,
        CONDITIONS: {conditions.WEEKDAY: True},
        USE_FOR_ROUTES_AT_STOP: True,
    },
    "weekend": {
        SOURCE: models.ServiceMapGroup.ServiceMapSource.SCHEDULE,
        THRESHOLD: 0.1,
        CONDITIONS: {conditions.WEEKEND: True},
        USE_FOR_ROUTES_AT_STOP: True,
    },
    "realtime": {
        SOURCE: models.ServiceMapGroup.ServiceMapSource.REALTIME,
        USE_FOR_STOPS_IN_ROUTE: True,
        USE_FOR_ROUTES_AT_STOP: True,
    },
}

_schema = Map(
    {
        NAME: Str(),
        Optional(PREFERRED_ID): Str(),
        Optional(TIMEZONE): Timezone(),
        Optional(REQUIRED_SETTINGS, []): Seq(Str()) | EmptyList(),
        Optional(REQUIREMENTS, {PACKAGES: [], SETTINGS: []}): Map(  # Ignored
            {
                Optional(PACKAGES, []): Seq(Str()) | EmptyList(),
                Optional(SETTINGS, []): Seq(Str()) | EmptyList(),
            }
        ),
        FEEDS: MapPattern(
            Str(),
            Map(
                {
                    HTTP: Map(
                        {
                            URL: Str(),
                            Optional(HEADERS, {}): MapPattern(Str(), Str())
                            | EmptyDict(),
                            Optional(TIMEOUT): HumanReadableTimePeriod(),
                        }
                    ),
                    PARSER: Map(
                        {
                            Optional(BUILT_IN, None): PyEnum(models.Feed.BuiltInParser),
                            Optional(CUSTOM, None): Str(),
                            Optional(OPTIONS): MapPattern(Str(), Any()) | EmptyDict(),
                        }
                    ),
                    Optional(AUTO_UPDATE, {ENABLED: False, PERIOD: -1}): Map(
                        {
                            Optional(ENABLED, True): Bool(),
                            Optional(PERIOD, -1): HumanReadableTimePeriod(),
                        }
                    ),
                    Optional(REQUIRED_FOR_INSTALL, False): Bool(),
                }
            ),
        ),
        Optional(SERVICE_MAPS, default_service_map_config): MapPattern(
            Str(),
            Map(
                {
                    SOURCE: PyEnum(models.ServiceMapGroup.ServiceMapSource),
                    Optional(THRESHOLD, 0): Float(),
                    Optional(CONDITIONS, None): ServiceMapConditions(),
                    Optional(USE_FOR_STOPS_IN_ROUTE, False): Bool(),
                    Optional(USE_FOR_ROUTES_AT_STOP, False): Bool(),
                }
            ),
        )
        | EmptyDict(),
    }
)


def render_template(jinja_yaml_template, setting_to_value=None):
    if setting_to_value is None:
        setting_to_value = {}
    try:
        return jinja2.Template(jinja_yaml_template).render(**setting_to_value)
    except jinja2.TemplateError as error:
        raise exceptions.InvalidSystemConfigFile(
            "The Jinja template is invalid\n" + str(error)
        )


def read(yaml_string, setting_to_value=None, label="transit system config"):
    if setting_to_value is None:
        setting_to_value = {}
    try:
        config = strictyaml.load(yaml_string, _schema, label=label).data
    except strictyaml.YAMLValidationError as error:
        raise exceptions.InvalidSystemConfigFile(
            "System config is valid YAML but is not a valid system config\n"
            + str(error)
        )
    except strictyaml.YAMLError as error:
        raise exceptions.InvalidSystemConfigFile(
            "Provided system config file cannot be parsed as YAML\n" + str(error)
        )

    required_settings = config[REQUIREMENTS][SETTINGS]
    missing_settings = set(required_settings) - set(setting_to_value.keys())
    if len(missing_settings) > 0:
        raise exceptions.InstallError(
            "Missing required settings: {}".format(", ".join(missing_settings))
        )

    return config
