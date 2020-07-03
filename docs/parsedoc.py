"""
Script to build the feed parsers API reference automatically using the Transiter
Python code.
"""

import dataclasses
import datetime
import enum
import inspect
import typing


def convert_type_to_type_desc(type_, default, plural=False):
    if plural:
        s = "s"
    else:
        s = ""
    if getattr(type_, "__origin__", None) == typing.Union:
        type_ = type_.__args__[0]
    if isinstance(type_, typing.ForwardRef):
        # type_ = type_.__args__[0]
        return f"Object{s} of type `{type_.__forward_arg__}`."
    if getattr(type_, "__origin__", None) == list:
        base = convert_type_to_type_desc(
            type_.__args__[0], dataclasses.MISSING, plural=True
        )
        return "List of " + base[0].lower() + base[1:]
    if type_ == str:
        return f"String{s}."
    if type_ == int:
        return "Integer."
    if type_ == float:
        return "Float."
    if type_ == bool:
        return "Boolean."
    if type_ == datetime.datetime:
        return (
            "Datetime object. "
            "If no timezone is provided, the importer will add the timezone of the transit system to it."
        )
    if type_ == datetime.date:
        return f"Date object{s}."
    if type_ == datetime.time:
        return f"Time object{s}."
    if getattr(type_, "__fk_type__", None) is not None:
        return f"String foreign key reference{s} to the `{type_.__fk_field__}` attribute of the `{type_.__fk_type__.__name__}` class."

    if issubclass(type_, enum.Enum):
        enum_values = ["`{}`".format(e.name) for e in type_]
        result = (
            f"Enum constant{s} of type `transiter.parse.{type_.__qualname__}`; "
            f"admissible values are: {', '.join(enum_values)}."
        )
        if default is not dataclasses.MISSING:
            result += f" Default is `{default.name}`."
        return result

    raise ValueError


def process(parse_type, f, first):
    # print(parse_type.__doc__)
    lines = []
    lines.extend(
        [
            "{} {}".format("##" if first else "###", parse_type.__name__),
            "",
            inspect.cleandoc(parse_type.__doc__),
            "",
            "Name | Type",
            "-----|-----",
        ]
    )
    for a in dataclasses.fields(parse_type):
        if (
            a.default is dataclasses.MISSING
            and a.default_factory is dataclasses.MISSING
        ):
            star = "*"
        else:
            star = ""

        lines.append(
            "{}{} | {}".format(
                a.name, star, convert_type_to_type_desc(a.type, a.default)
            )
        )
    lines.extend(["", "*required"])
    print("\n".join(lines), file=f)


# process(parse.Route)
# process(parse.Trip)


def resolve_dependencies(key_to_object):
    key_to_children = {}
    non_root_keys = set()
    for key, object_ in key_to_object.items():
        if not dataclasses.is_dataclass(object_):
            continue
        key_to_children[key] = [key]
        for field in dataclasses.fields(object_):
            # Check that object is of type typing.List
            if getattr(field.type, "__origin__", None) != list:
                continue
            contents_type = field.type.__args__[0]
            if not isinstance(contents_type, typing.ForwardRef):
                continue
            child = contents_type.__forward_arg__
            key_to_children[key].append(child)
            non_root_keys.add(child)

    for key in sorted(key_to_children.keys()):
        if key in non_root_keys:
            continue
        yield [key_to_object[ancestor] for ancestor in _ancestors(key, key_to_children)]


def _ancestors(root, key_to_children):
    for child in key_to_children[root]:
        if child == root:
            yield child
            continue
        yield from _ancestors(child, key_to_children)


# TODO: take the file name as a command line argument
# TODO: make this relative to the file location
with open("transiter/parse/types.py") as f:
    parse = {}
    exec(f.read(), parse)

with open("docs/docs/parser-output-types.md", "w") as f:
    print(parse["__doc__"], file=f)

    dependencies = list(resolve_dependencies(parse))
    print(
        f"Transiter feed parsers can return one of {len(dependencies)} types:\n", file=f
    )
    for elements in dependencies:
        print(f"- [{elements[0].__name__}](#{elements[0].__name__.lower()})\n", file=f)

    for elements in dependencies:
        first = True
        for element in elements:
            process(element, f, first)
            first = False
