from realtimerail.data import schema
import sqlalchemy
import csv
from realtimerail.algorithms import topologicalsort
#routegraphconstructor

topologicalsort.test()


exit()

with open('staticdata/mta/stop_times.txt', mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    routegraphconstructor.construct(csv_reader)


exit()


def create_database():
    engine = sqlalchemy.create_engine("postgres://james@/postgres")
    conn = engine.connect()
    try:
        conn.execute("commit")
        conn.execute("DROP DATABASE realtimerail")
    except sqlalchemy.exc.ProgrammingError:
        pass
    conn.execute("commit")
    conn.execute("CREATE DATABASE realtimerail")
    conn.close()
    pass


def create_tables():
    engine = sqlalchemy.create_engine("postgres://james@/realtimerail")
    schema.Base.metadata.create_all(engine)

    pass


def mta_trip_id_to_data():
    pass

    #construct route graph algorithm - given time

    #returns (route, day)
    # for each line, find all northbound unqiue trips that
    #  start between 1pm and 2pm (for day and weekend service) mista
    #
    # and say (1am and 2am for late night)
    # unqiue route has is just some hash of the concatenation of the stop_ids

    # use this to construct a graph of service. Do some topoligical sort
    # then to get a linear listing (but retain graph information?)
    # We could store the route graph in the database using self-referencing
    # columns)


    #will need to override this for the Z train

def populate_tables():

    engine = sqlalchemy.create_engine("postgres://james@/realtimerail")
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()


    with open('staticdata/mta/routes.txt', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            print(row['route_id'])
            print(row['route_color'])
            route = schema.Route()
            session.add(route)
            route.route_id=row['route_id']
            route.color = row['route_color']
            route.timetable_url = row['route_url']
            route.short_name = row['route_short_name']
            route.long_name = row['route_long_name']
            route.description = row['route_desc']


    station_sets_by_stop_id = {}
    stops_by_stop_id = {}
    with open('staticdata/mta/stops.txt', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            stop_id = row['stop_id']
            if stop_id[-1] == 'N' or stop_id[-1] == 'S':
                continue
            print(row['stop_id'])
            stop = schema.Stop()
            session.add(stop)
            stop.stop_id=row['stop_id']
            stop.name = row['stop_name']
            stop.longitude = row['stop_lon']
            stop.lattitude = row['stop_lat']

            station_sets_by_stop_id[stop_id] = set([stop_id])
            stops_by_stop_id[stop_id] = stop

    with open('staticdata/mta/transfers.txt', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            stop_id_1 = row['from_stop_id']
            stop_id_2 = row['to_stop_id']
            if stop_id_1 == stop_id_2:
                continue

            station_set = station_sets_by_stop_id[stop_id_1].union(
                station_sets_by_stop_id[stop_id_2])
            for stop_id in station_set:
                station_sets_by_stop_id[stop_id] = station_set

        for station_set in station_sets_by_stop_id.values():
            if len(station_set) == 0:
                continue

            station = schema.Station()
            session.add(station)
            for stop_id in station_set:
                stops_by_stop_id[stop_id].station = station
            station_set.clear()

    sorted_stop_ids = sorted(stops_by_stop_id.keys())
    index = 0
    with open('staticdata/custom/direction_names.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            while(sorted_stop_ids[index] != row['stop_id']):

                north = schema.DirectionName()



                session.add(north)
                north.name = row['north_direction_name']
                north.track = None
                north.direction = 'N'
                north.stop = stops_by_stop_id[sorted_stop_ids[index]]

                south = schema.DirectionName()
                session.add(south)
                south.name = row['south_direction_name']
                south.track = None
                south.direction = 'S'
                south.stop = stops_by_stop_id[sorted_stop_ids[index]]

                #south = schema.DirectionName()
                #print('{},{},{}'.format(sorted_stop_ids[index],
                #    row['north_direction_name'], row['south_direction_name']))
                index += 1

    with open('staticdata/custom/direction_name_exceptions.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            direction = schema.DirectionName()
            session.add(direction)
            direction.name = row['name']
            direction.track = row['track']
            direction.direction = row['direction']
            direction.stop = stops_by_stop_id[row['stop_id']]


    print(sorted_stop_ids)
    session.commit()


# The data imported here so far should be enough to build the basic
# route, stop and station services



a = dict()
a['a'] = set()
a['b'] = a['a']

a['b'].add('c')

print(a)

if(False):
    pass

if(True):
    create_database()

    create_tables()

    populate_tables()

#Base.metadata.create_all(engine)
