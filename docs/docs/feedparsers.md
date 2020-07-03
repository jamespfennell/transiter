# Writing custom feed parsers

## Introduction

Transiter has built-in support for the GTFS static and GTFS realtime feed formats.
However, many transit agencies distribute data in custom feed formats,
    or extensions of the GTFS formats.
For example, in the past many transit agencies distributed alerts data in XML formats.
To support these use cases, Transiter has a system for providing _custom feed parsers_.
Custom feed parsers enable arbitrary feeds to be read into Transiter.
The only constraint is that that data must be convertible into 
[Transiter's parser output types](parser-output-types.md).

!!! tip "Adding extra fields to the parser types"

    If you have a piece of data you want to import that doesn't
    translate well onto the parser output types, feel free
    to open a request on the Transiter Github repo for an appropriate 
    field or type to be added.

## Simple feed parsers

There are two ways to write custom feed parsers, and
    we'll begin with the simple case.
A simple feed parser is just a Python function that converts binary
    data into Transiter parser output types.
The binary data is just the raw data 
    from the HTTP request for that feed, and is inputted as the `content`
    argument to the function.

### Example

Suppose that a transit agency distributes
alerts in CSV format, so that an instance of the feed looks something like this:

```text
alert_id,alert_name,alert_text,affected_route
12345,Delays,Delays in southbound A service,A
```

Here's a simple Transiter parser that reads this format:

```python
import csv

from transiter import parse

def parser(content):
    lines = content.decode("utf-8")
    csv_reader = csv.DictReader(lines)
    for row in csv_reader:
        alert = parse.Alert(
            id=row["alert_id"],
            route_ids = [row["affected_route"]],
            messages = [
                parse.AlertMessage(
                    header = row["alert_name"],
                    description = row["alert_text"]
                )   
            ]           
        )       
        yield alert
```

In general, the parser just has to return an iterator of Transiter
    parser output types.
In this example, the `yield` keyword is used to return such an iterator.
We could have as easily returned a `list` of Alerts instead.


## Registering your feed parser with Transiter

After writing a custom feed parser, you need to instruct
Transiter to use it for reading specific feeds.
First, you must place your feed parser in a Python package
and install that package in the Python environment that Transiter
is running in.
Then, in the system configuration YAML file for the transit system
you're working with, specify the custom parser:

```yaml
feeds:

  myfeed:
    http:
      url: 'http://www.transitagency.com/feed'  # the URL the feed is at
    parser:
      custom: 'mypackage.mymodule:parser_function'  # specifying the parser
```

Note that parsers are specified in the form
`package:function`.


## Class based parsers

Simple feed parsers are nice because the API is easy to uderstand and work with.
However the simple feed parser API has some limitations, including:

- It's difficult to transmit additional metadata, such as the timestamp of the feed.

- While it's clear how we could pass options to the feed parser (using a function argument),
    there would be no way to verify an options set is valid without actually providing
    some binary data too.
    
- Transiter cannot, in general, know what kinds of output types your parser returns.
    This means Transiter has to do extra work to account for the possibility that your 
    parser returns every possible output type.
    
To solve these problems, there is also a class based API for defining parsers.
A class based parser is:

- A subclass of the class `transiter.parse.TransiterParser`.

- This subclass must implement the method `load_content`. 
    This method takes a single argument `content`, which is the binary content for the feed.
    
- For any Transiter output type the parser outputs, the associated getter
    method of the class must be implemented. 
    For example, if the parser outputs routes, then it must implement the `get_routes`
    method.
    
- The class can optionally implement the `get_timestamp` method, which
    outputs the time of the feed in `datetime.datetime` format.
    
- The class can optionally implement the `load_options` method.
    This method provided a mechanism for parser options to be defined in the 
    system configuration YAML file and passed into the parser.
    The `load_options` method takes a single method `options_blob` which 
    a JSON blob containing the options data from the YAML file.


### Example

To see how this works, we can re-write the alerts simple parser above
using the class based approach.
It looks something like this:


```python
import csv
import typing

from transiter import parse

class AlertsParser(parse.TransiterParser):
    
    def load_content(self, content: bytes) -> None:
        self.content = content
    
    def get_alerts(self) -> typing.Iterable[parse.Alert]:
        lines = self.content.decode("utf-8")
        csv_reader = csv.DictReader(lines)
        for row in csv_reader:
            alert = parse.Alert(
                id=row["alert_id"],
                route_ids = [row["affected_route"]],
                messages = [
                    parse.AlertMessage(
                        header = row["alert_name"],
                        description = row["alert_text"]
                    )   
                ]           
            )       
            yield alert
```

Notes:

- There is a lot of flexibility on where the parsing occurs, 
    either in the `load_content` method or `get_alerts` method.
    In this case we've opted to just store the content as an instance variable
    and keep all the logic in the getter function.
    
- The parser is specified in the system config yaml in the form `package:ParserClass`.


## Working with GTFS realtime extensions

The GTFS Realtime format supports extensions, which provide
a mechanism for transit agencies to provide additional data
in their realtime feeds that, they judge, does not fit into the standard spec.
The NYC Subway realtime feed is an example of a feed using a GTFS Realtime extension.
These feeds can be successfully parsed using the default Transiter GTFS Realtime parser,
    but all of the data in the extension will be ignored.

The Transiter GTFS Realtime parser was designed
    to enable customization so that extension data can be parsed.
Reading extension data involves creating a custom parser subclassed from the
    built-in GTFS Realtime parser.
This way, most of the logic in the built-in parser can be re-used.

To read extension data, the following is required:

1. A module for reading the extended GTFS Realtime feed data.
   This is typically the standard `google.transit.gtfs_realtime_pb2`
   module with some alteration made so that the protobuf extension data
   can be read.

2. A custom parser which is a class based parser inherited from
    the built-in GTFS Realtime parser.
    The built-in parser is accessible at `tranister.parse.GtfsRealtimeParser`.
   
3. The custom parser must specify the module 
    used to read the feed in the class variable `GTFS_REALTIME_PB2_MODULE`.

4. Finally, the static method `post_process_feed_message` should
    be implemented to perform the necessary data transformations.
    This static method takes a single parameter `feed_message`
    which is the root message of the GTFS feed.
    

### Example

As an example, we'll illustrate how to read one piece of extension
data in the NYC Subway feed.

The NYC Subway extensions adds extra data to the GTFS Realtime `TripDescriptor` type
    in a new `NyctTripDescriptor` type.
One of the fields of the `NyctTripDescriptor` is an enum `direction`
    which in practice can either be `NORTH=0` or `SOUTH=2  `.
The subway feed does _not_ provide a direction ID in the `TripDescriptor`.
The transformation we make here is to convert the custom `direction`
type to the standard `direction_id` type, according to the rule that
`NORTH` gets mapped to `True` and `SOUTH` to `False`.
This way the direction can be read normally by Transiter and interpreted 
in the normal way by consumers without any more custom logic.

Here's how this can be implemented:

```python
# The compiled protobuf reader with the NYC Subway extension included.
# Assumed to be importable from the current package in this example.
from . import nyc_subway_gtfs_rt_pb2

from transiter import parse

class NYCSubwayParser(parse.GtfsRealtimeParser):

    GTFS_REALTIME_PB2_MODULE = nyc_subway_gtfs_rt_pb2

    @staticmethod
    def post_process_feed_message(feed_message):
        for entity in feed_message.entity:
            if not entity.HasField("trip_update"):
                continue
            trip = entity.trip_update.trip
            # NOTE: 1001 is the NYC Subways extension ID.
            mta_extension = trip.Extensions[1001]
            if mta_extension.direction == "0":
                trip.direction_id = 0  # True
            else:
                trip.direction_id = 1  # False
```

### The Transiter GTFS Extension

Transiter has its own GTFS Extension to enable
    importing data, like the `track` of a trip stop time,
    that doesn't appear in the GTFS Realtime spec.
Any data that is placed on the Transiter extension will be read
    successfully by the GTFS Realtime parser.
Consult [the protobuf definition](https://github.com/jamespfennell/transiter/blob/master/transiter/parse/transiter_gtfs_rt_pb2/gtfs-realtime-transiter-extension.proto) for data that it supports.
    
