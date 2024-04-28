import dataclasses
import requests
import typing


class ApiType:
    @classmethod
    def from_api(cls, api_response):
        d = {}
        for field in dataclasses.fields(cls):
            value = api_response.get(field.name)
            if typing.get_origin(field.type) is list:
                element_type = typing.get_args(field.type)[0]
                assert issubclass(element_type, ApiType)
                value = [element_type.from_api(elem) for elem in value]
            elif issubclass(field.type, ApiType):
                if value is not None:
                    value = field.type.from_api(value)
            elif issubclass(field.type, int):
                if value is not None:
                    value = int(value)
            d[field.name] = value
        return cls(**d)


@dataclasses.dataclass
class StopReference(ApiType):
    id: str


@dataclasses.dataclass
class ChildResources(ApiType):
    count: int


@dataclasses.dataclass
class System(ApiType):
    id: str
    stops: ChildResources
    routes: ChildResources


@dataclasses.dataclass
class Route(ApiType):
    id: str
    shortName: str
    longName: str
    color: str
    textColor: str
    description: str
    url: str
    sortOrder: int
    continuousPickup: str
    continuousDropOff: str
    type: str


@dataclasses.dataclass
class Stop(ApiType):
    id: str
    code: str
    name: str
    description: str
    zoneId: str
    latitude: float
    longitude: float
    url: str
    type: str
    wheelchairBoarding: bool
    timezone: str
    platformCode: str
    parentStop: StopReference
    childStops: typing.List[StopReference]


@dataclasses.dataclass
class ListStopsResponse(ApiType):
    stops: typing.List[Stop]


@dataclasses.dataclass
class ListRoutesResponse(ApiType):
    routes: typing.List[Route]


class TransiterClient:
    def __init__(self, transiter_host):
        self._transiter_host = transiter_host

    def _get(self, cls: ApiType, relative_url: str, params={}):
        return cls.from_api(
            requests.get(f"{self._transiter_host}/{relative_url}", params=params).json()
        )

    def get_system(self, system_id: str) -> System:
        return self._get(System, f"systems/{system_id}")

    def list_stops(self, system_id: str, params={}) -> ListStopsResponse:
        return self._get(ListStopsResponse, f"systems/{system_id}/stops", params)

    def get_stop(self, system_id: str, stop_id: str) -> Stop:
        return self._get(Stop, f"systems/{system_id}/stops/{stop_id}")

    def list_routes(self, system_id: str, params={}) -> ListRoutesResponse:
        return self._get(ListRoutesResponse, f"systems/{system_id}/routes", params)

    def get_route(self, system_id: str, route_id: str) -> Route:
        return self._get(Route, f"systems/{system_id}/routes/{route_id}")
