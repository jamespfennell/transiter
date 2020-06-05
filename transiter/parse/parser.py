import datetime
import typing

from transiter.parse import types as parse


class TransiterParser:
    """
    Transiter's public parser API.

    This class is used to implement arbitrary parsers in Transiter. These can be used
    to read any kind of transit data into Transiter as long as the data can be pivoted
    to transiter.parse data types.

    To create a custom parser, subclass this class. You must implement the load_content
    method. Other than that, you implement methods based on which types your parser
    can return. For example, if your parser returns data of type transiter.parse.Stop,
    implement the get_stops method to return these entities.
    """

    def load_options(self, options_blob: typing.Optional[dict]) -> None:
        """
        Load options into the parser.

        Options are provided by users in the system definition yaml file, and the
        resulting JSON blob is inputted here as options_blob. For example, if the user
        specifies:

          parser:
            custom: "package:module"
            options:
              option_a: "value"
              option_b:
                - "a"
                - "b"

        then options_blob will be:

          {
            "option_a": "value",
            "option_b": ["a", "b"]
          }

        The blob can contain dictionaries, lists and strings only.

        It's generally encouraged to fail hard if the options blob does not have the
        right structure or if it has additional fields. This will give early feedback to
        the administrator on unexpected parse results.
        """

    def load_content(self, content: bytes) -> None:
        """
        Load content from a feed into the parser.

        Note that in many parser implementations this will simply involve:

            self._content = content

        However many parsers have more logic at this point.
        """
        raise NotImplementedError  # pragma: no cover

    def get_timestamp(self) -> typing.Optional[datetime.datetime]:
        pass  # pragma: no cover

    def get_agencies(self) -> typing.Iterable[parse.Agency]:
        pass  # pragma: no cover

    def get_routes(self) -> typing.Iterable[parse.Route]:
        pass  # pragma: no cover

    def get_stops(self) -> typing.Iterable[parse.Stop]:
        pass  # pragma: no cover

    def get_transfers(self) -> typing.Iterable[parse.Transfer]:
        pass  # pragma: no cover

    def get_scheduled_services(self) -> typing.Iterable[parse.ScheduledService]:
        pass  # pragma: no cover

    def get_trips(self) -> typing.Iterable[parse.Trip]:
        pass  # pragma: no cover

    def get_vehicles(self) -> typing.Iterable[parse.Vehicle]:
        pass  # pragma: no cover

    def get_alerts(self) -> typing.Iterable[parse.Alert]:
        pass  # pragma: no cover

    def get_direction_rules(self) -> typing.Iterable[parse.DirectionRule]:
        pass  # pragma: no cover

    # The rest of this class is not a part of the public API, and may be changed!
    # Developers are strongly discouraged from changing any data types or methods
    # below when implementing this class.

    __type_to_method__ = {
        parse.Agency: get_agencies,
        parse.Route: get_routes,
        parse.Stop: get_stops,
        parse.Transfer: get_transfers,
        parse.ScheduledService: get_scheduled_services,
        parse.Trip: get_trips,
        parse.Vehicle: get_vehicles,
        parse.Alert: get_alerts,
        parse.DirectionRule: get_direction_rules,
    }

    @property
    def supported_types(self):
        """
        Return a set of transiter.parse types that are supported by this parser.
        """
        return set(
            type_
            for type_ in self.__type_to_method__.keys()
            if self._get_entities_getter(type_) is not None
        )

    def get_entities(self, entity_type):
        """
        Return an iterator of entities of a given type.

        This method ultimately calls the relevant getter method above; for example,
        with entity_type=parse.Route, this returns the result of get_routes above.

        If the method has not been implemented, then a NotImplementedError is raised.
        """
        method = self._get_entities_getter(entity_type)
        if method is None:
            raise NotImplementedError(
                "This parser does not support entities of type transiter.parse.{}.".format(
                    entity_type.__name__
                )
            )
        # Using `iter` here instead of `yield from` means the NotImplementedError above
        # is raised as soon as the method is called, rather than when the iteration
        # begins.
        return iter(method())

    def _get_entities_getter(self, entity_type):
        """
        Get the entities getter corresponding to a given type.

        This method returns None if the method has not been implemented.
        """
        abstract_method = self.__type_to_method__[entity_type]
        method = getattr(self, abstract_method.__name__)
        if method.__func__ is abstract_method:
            return None
        return method


class CallableBasedParser(TransiterParser):
    """
    Parser that uses the results of a Python callable to generate entities.

    This implements Transiter's simple parser API, whereby a parser can be a simple
    callable that returns entities of type transiter.parser.
    """

    def __init__(self, callable_: typing.Callable):
        self._callable = callable_
        self._type_to_entities = {type_: [] for type_ in self.__type_to_method__.keys()}

    def load_content(self, content: bytes) -> None:
        for entity in self._callable(content):
            type_ = type(entity)
            if type_ not in self._type_to_entities:
                raise TypeError("Unsupported parser type {}!".format(type_))
            self._type_to_entities[type_].append(entity)

    @property
    def supported_types(self):
        return set(self.__type_to_method__.keys())

    def get_entities(self, entity_type):
        return self._type_to_entities[entity_type]

    def __eq__(self, other):
        return self._callable is other._callable


def cast_object_to_instantiated_transiter_parser(object_):
    """
    Given an object, return an instantiated Transiter parser associated to that object.

    If the object is a TransiterParser type, the object itself is returned.
    Otherwise, if it is a callable, a CallableBasedParser using that callable is
    returned. Otherwise, a ValueError will be raised.
    """
    if isinstance(object_, type) and issubclass(object_, TransiterParser):
        return object_()
    if callable(object_):
        return CallableBasedParser(object_)
    raise ValueError("Cannot instantiate {} as a Transiter parser.".format(object_))
