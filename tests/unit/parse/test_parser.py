from transiter import parse
import pytest

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

    assert parser.supported_types == {parse.Route, parse.Stop, parse.ScheduledService}


def test_cast__transiter_parser():
    parser = ImplementedParser()

    assert parser is parse.parser.cast_object_to_transiter_parser(parser)


def test_cast__callable():
    def entities(content_):
        return []

    result = parse.parser.cast_object_to_transiter_parser(entities)

    assert isinstance(result, parse.parser.CallableBasedParser)
    assert result._callable is entities


def test_cast__error():
    with pytest.raises(ValueError):
        parse.parser.cast_object_to_transiter_parser("")
