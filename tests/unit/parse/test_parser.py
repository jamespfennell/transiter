import pytest

from transiter import parse
from transiter.db.models import updatableentity

route = parse.Route(id="route", type=parse.Route.Type.RAIL)


class ImplementedParser(parse.TransiterParser):
    def load_content(self, content: bytes) -> None:
        pass

    def get_routes(self):
        return [route]


def test_supported_types():
    parser = ImplementedParser()

    assert {parse.Route} == parser.supported_types


def test_get_entities():
    parser = ImplementedParser()

    assert [route] == list(parser.get_entities(parse.Route))


def test_get_entities__not_implemented():
    parser = ImplementedParser()

    with pytest.raises(NotImplementedError):
        parser.get_entities(parse.Stop)


def test_callable_based_parser__invalid_callable():
    def entities(content_):
        return [""]

    parser = parse.parser.CallableBasedParser(entities)

    with pytest.raises(TypeError):
        parser.load_content(b"")


def test_callable_based_parser__get_entities():
    def entities(content_):
        return [route]

    parser = parse.parser.CallableBasedParser(entities)

    parser.load_content(b"")

    assert [route] == parser.get_entities(parse.Route)
    assert [] == parser.get_entities(parse.Stop)


def test_callable_based_parser__supported_types():
    def entities(content_):
        return [route]

    parser = parse.parser.CallableBasedParser(entities)

    assert parser.supported_types == set(updatableentity.list_feed_entities())


def test_cast__transiter_parser():
    assert isinstance(
        parse.parser.cast_object_to_instantiated_transiter_parser(ImplementedParser),
        ImplementedParser,
    )


def test_cast__callable():
    def entities(content_):
        return []

    result = parse.parser.cast_object_to_instantiated_transiter_parser(entities)

    assert isinstance(result, parse.parser.CallableBasedParser)
    assert result._callable is entities


def test_cast__error():
    with pytest.raises(ValueError):
        parse.parser.cast_object_to_instantiated_transiter_parser("")
