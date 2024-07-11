import dataclasses
import requests
import typing
import time


@dataclasses.dataclass
class ApiType:
    @classmethod
    def from_api(cls, api_response):
        d = {}
        for field in dataclasses.fields(cls):
            value = api_response.get(field.name)
            field_type = field.type

            # Handle Optional types
            if typing.get_origin(field_type) is typing.Union:
                args = typing.get_args(field_type)
                if len(args) == 2 and type(None) in args:
                    field_type = args[0] if args[1] is type(None) else args[1]
            if typing.get_origin(field_type) is list:
                element_type = typing.get_args(field_type)[0]
                assert issubclass(element_type, ApiType)
                value = [element_type.from_api(elem) for elem in value] if value is not None else None
            elif issubclass(field_type, ApiType):
                if value is not None:
                    value = field_type.from_api(value)
            elif field_type is int:
                if value is not None:
                    value = int(value)
            elif field_type is str:
                if value is not None:
                    value = str(value)
            elif field_type is float:
                if value is not None:
                    value = float(value)
            d[field.name] = value

        return cls(**d)


@dataclasses.dataclass
class ShapeReference(ApiType):
    id: str
    # todo: system, resource


@dataclasses.dataclass
class StopReference(ApiType):
    id: str
    # todo: system, resource


@dataclasses.dataclass
class VehicleReference(ApiType):
    id: str
    # todo: system, resource


@dataclasses.dataclass
class RouteReference(ApiType):
    id: str
    # todo: system, resource


@dataclasses.dataclass
class TripReference(ApiType):
    id: str
    route: RouteReference
    directionId: bool
    # todo: system, resource


@dataclasses.dataclass
class AlertReference(ApiType):
    id: str
    # todo: system, resource
    cause: str
    effect: str


@dataclasses.dataclass
class ChildResources(ApiType):
    count: int
    path: str


@dataclasses.dataclass
class ServiceMapAtStop(ApiType):
    configId: str
    routes: typing.List[RouteReference]


@dataclasses.dataclass
class ServiceMapInRoute(ApiType):
    configId: str
    stops: typing.List[StopReference]


@dataclasses.dataclass
class System(ApiType):
    id: str
    name: str
    # todo: resource
    status: str
    agencies: ChildResources
    feeds: ChildResources
    routes: ChildResources
    stops: ChildResources
    transfers: ChildResources


@dataclasses.dataclass
class Agency(ApiType):
    id: str
    # todo: system, resource
    name: str
    url: str
    timezone: str
    language: str
    phone: str
    fareUrl: str
    email: str
    # todo: routes
    alerts: typing.List[AlertReference]


@dataclasses.dataclass
class AlertActivePeriod(ApiType):
    startsAt: int
    endsAt: int


@dataclasses.dataclass
class AlertText(ApiType):
    text: str
    language: str


@dataclasses.dataclass
class Alert(ApiType):
    id: str
    # todo: system, resource
    cause: str
    effect: str
    currentActivePeriod: AlertActivePeriod
    allActivePeriods: typing.List[AlertActivePeriod]
    header: typing.List[AlertText]
    description: typing.List[AlertText]
    url: typing.List[AlertText]


@dataclasses.dataclass
class Feed(ApiType):
    id: str
    lastSuccessfulUpdateMs: int
    lastSkippedUpdateMs: int
    lastFailedUpdateMs: int


@dataclasses.dataclass
class Transfer(ApiType):
    id: str
    # todo: system, resource
    fromStop: StopReference
    toStop: StopReference
    type: str
    minTransferTime: int


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
    serviceMaps: typing.List[ServiceMapInRoute]
    alerts: typing.List[AlertReference]


@dataclasses.dataclass
class ShapePoint(ApiType):
    latitude: float
    longitude: float
    distance: float


@dataclasses.dataclass
class Shape(ApiType):
    id: str
    # todo: system, resource
    points: typing.List[ShapePoint]


@dataclasses.dataclass
class EstimatedTime(ApiType):
    time: int


@dataclasses.dataclass
class StopTime(ApiType):
    trip: TripReference
    arrival: EstimatedTime
    departure: EstimatedTime
    stopSequence: int
    future: bool
    headsign: typing.Optional[str] = None


@dataclasses.dataclass
class Stop(ApiType):
    id: str
    # todo: system, resource
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
    transfers: typing.List[Transfer]
    serviceMaps: typing.List[ServiceMapAtStop]
    alerts: typing.List[AlertReference]
    stopTimes: typing.List[StopTime]


@dataclasses.dataclass
class Trip(ApiType):
    id: str
    # todo: system, resource
    shape: ShapeReference
    vehicle: VehicleReference
    stopTimes: typing.List[StopTime]


@dataclasses.dataclass
class Vehicle(ApiType):
    id: str
    # todo: system, resource
    trip: TripReference
    latitude: float
    longitude: float


@dataclasses.dataclass
class ListShapesResponse(ApiType):
    shapes: typing.List[Shape]
    nextId: str


@dataclasses.dataclass
class ListStopsResponse(ApiType):
    stops: typing.List[Stop]
    nextId: str


@dataclasses.dataclass
class ListVehiclesResponse(ApiType):
    vehicles: typing.List[Vehicle]
    nextId: str


@dataclasses.dataclass
class ListAgenciesResponse(ApiType):
    agencies: typing.List[Agency]


@dataclasses.dataclass
class ListFeedsResponse(ApiType):
    feeds: typing.List[Feed]


@dataclasses.dataclass
class ListAlertsResponse(ApiType):
    alerts: typing.List[Alert]


@dataclasses.dataclass
class ListTransfersResponse(ApiType):
    transfers: typing.List[Transfer]


@dataclasses.dataclass
class ListRoutesResponse(ApiType):
    routes: typing.List[Route]


class TransiterClient:
    def __init__(self, transiter_host):
        self._transiter_host = transiter_host

    def get(self, relative_url: str, params={}):
        return requests.get(f"{self._transiter_host}/{relative_url}", params=params)

    def _get_typed(self, cls: ApiType, relative_url: str, params={}):
        r = requests.get(f"{self._transiter_host}/{relative_url}", params=params)
        r.raise_for_status()
        j = r.json()
        return cls.from_api(j)

    def install_system(self, system_id: str, system_config: str):
        requests.put(
            f"{self._transiter_host}/systems/{system_id}",
            json={
                "yaml_config": {
                    "content": system_config,
                },
            },
        ).raise_for_status()
        for _ in range(100):
            system = self.get_system(system_id)
            if system.status not in {"INSTALLING", "UPDATING"}:
                break
            time.sleep(0.05)
        assert system.status == "ACTIVE"

    def get_system(self, system_id: str) -> System:
        return self._get_typed(System, f"systems/{system_id}")

    def delete_system(self, system_id: str):
        response = requests.delete(f"{self._transiter_host}/systems/{system_id}")
        if response.status_code == 404:
            return
        response.raise_for_status()

    def perform_feed_update(self, system_id: str, feed_id: str):
        r = requests.post(f"{self._transiter_host}/systems/{system_id}/feeds/{feed_id}")
        r.raise_for_status()
        j = r.json()
        assert j["feedUpdate"]["status"] in {"UPDATED", "SKIPPED"}, f"feed update: {j}"

    def list_agencies(self, system_id: str) -> ListAgenciesResponse:
        return self._get_typed(ListAgenciesResponse, f"systems/{system_id}/agencies")

    def get_agency(self, system_id: str, agency_id: str) -> Agency:
        return self._get_typed(Agency, f"systems/{system_id}/agencies/{agency_id}")

    def list_alerts(self, system_id: str) -> ListAlertsResponse:
        return self._get_typed(ListAlertsResponse, f"systems/{system_id}/alerts")

    def get_alert(self, system_id: str, alert_id: str) -> Alert:
        return self._get_typed(Alert, f"systems/{system_id}/alerts/{alert_id}")

    def list_feeds(self, system_id: str) -> ListFeedsResponse:
        return self._get_typed(ListFeedsResponse, f"systems/{system_id}/feeds")

    def get_feed(self, system_id: str, feed_id: str) -> Feed:
        return self._get_typed(Feed, f"systems/{system_id}/feeds/{feed_id}")

    def list_shapes(self, system_id: str, params={}) -> ListShapesResponse:
        return self._get_typed(
            ListShapesResponse, f"systems/{system_id}/shapes", params
        )

    def get_shape(self, system_id: str, shape_id: str, params={}) -> Shape:
        return self._get_typed(Shape, f"systems/{system_id}/shapes/{shape_id}", params)

    def list_stops(self, system_id: str, params={}) -> ListStopsResponse:
        return self._get_typed(ListStopsResponse, f"systems/{system_id}/stops", params)

    def get_stop(self, system_id: str, stop_id: str, params={}) -> Stop:
        return self._get_typed(Stop, f"systems/{system_id}/stops/{stop_id}", params)

    def list_transfers(self, system_id: str) -> ListTransfersResponse:
        return self._get_typed(ListTransfersResponse, f"systems/{system_id}/transfers")

    def get_transfer(self, system_id: str, transfer_id: str) -> Transfer:
        return self._get_typed(Transfer, f"systems/{system_id}/transfers/{transfer_id}")

    def list_routes(self, system_id: str, params={}) -> ListRoutesResponse:
        return self._get_typed(
            ListRoutesResponse, f"systems/{system_id}/routes", params
        )

    def get_route(self, system_id: str, route_id: str, params={}) -> Route:
        return self._get_typed(Route, f"systems/{system_id}/routes/{route_id}", params)

    def get_trip(self, system_id: str, route_id: str, trip_id: str, params={}) -> Trip:
        return self._get_typed(
            Trip, f"systems/{system_id}/routes/{route_id}/trips/{trip_id}", params
        )

    def list_vehicles(self, system_id: str, params={}) -> ListVehiclesResponse:
        return self._get_typed(
            ListVehiclesResponse, f"systems/{system_id}/vehicles", params
        )

    def get_vehicle(self, system_id: str, vehicle_id: str, params={}) -> Vehicle:
        return self._get_typed(
            Vehicle, f"systems/{system_id}/vehicles/{vehicle_id}", params
        )
