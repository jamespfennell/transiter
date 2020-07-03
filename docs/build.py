"""
This Python script builds the subset of documentation pages that are generated
using documentation in the Transiter Python code.
"""

import dataclasses
import inspect
import typing

from transiter.http import endpoints, flaskapp
from transiter.http import httpmanager
from transiter.http.flaskapp import app

API_INDEX_BASE = """
# Endpoints list

Transiter's HTTP endpoints mostly return JSON data; exceptions are specifically noted.
In order to avoid stale documentation,
the structure of the JSON data returned by each endpoint
 is not described here, but can be inspected on the
[demo site](https://demo.transiter.io) or
by clicking any of the example links below.

!!! warning "Permissions levels"
    Every endpoint has an associated *permissions level* to enable access control.
    In production, you will likely *not* want to allow access to all endpoints - 
        for example, you will want to prohibit users from deleting systems.
    The [permissions documentation page](../deployment/permissions.md) describes
        the permissions system and how you can use it to deploy Transiter safely.

    If an endpoint does not describe a permissions level, then it does
    not impose any permissions restrictions.
"""


@dataclasses.dataclass
class Group:
    module: typing.Any
    extra_modules: list = dataclasses.field(default_factory=list)
    endpoints: list = dataclasses.field(default_factory=list)
    extra_endpoints: list = dataclasses.field(default_factory=list)

    def name(self):
        title, __ = clean_doc(self.module.__doc__)
        return title.replace(" ", "-").lower()

    def page(self):
        return f"api/{self.name()}.md".replace(" ", "-").lower()

    def all_modules(self):
        return [self.module] + self.extra_modules

    def all_endpoints(self):
        return self.endpoints + self.extra_endpoints


@dataclasses.dataclass
class Endpoint:
    title: str
    rule: str
    method: str
    doc: str
    module: str


def match_group(groups, endpoint_module):
    for group in groups:
        if endpoint_module in group.all_modules():
            return group
    return None


def clean_doc(raw_doc):
    if raw_doc is None:
        return "Title unknown", "No doc provided!"
    doc = inspect.cleandoc(raw_doc).strip()
    first_new_line = doc.find("\n")
    if first_new_line >= 0:
        title = doc[:first_new_line].strip()
        body = doc[first_new_line + 1 :]
    else:
        title = doc
        body = ""
    return title, body


def populate_endpoints(groups):
    func_to_rule = {}
    for rule in app.url_map.iter_rules():
        if rule.rule[-1] == "/" and rule.rule != "/" and rule.rule[:5] != "/docs":
            continue
        func_to_rule[app.view_functions[rule.endpoint]] = rule

    for endpoint in httpmanager.get_documented_endpoints():
        rule = func_to_rule.get(endpoint.func)
        if rule is None:
            print(f"Warning: no rule for function {endpoint.func}, skipping")
            continue
        del func_to_rule[endpoint.func]
        group = match_group(groups, inspect.getmodule(endpoint.func))
        if group is None:
            print(f"Warning: no group for {rule.endpoint}, skipping ")
            continue

        function = app.view_functions[rule.endpoint]
        doc = function.__doc__
        if doc is None:
            print(f"Warning: no documentation for {rule.endpoint}, skipping")
            continue

        title, body = clean_doc(doc)

        if title[-1] == ".":
            print(
                f"Warning: first line of documentation for {rule.endpoint} ends with a period, skipping."
            )
            continue

        if group.module is inspect.getmodule(endpoint.func):
            add_to = group.endpoints
        else:
            add_to = group.extra_endpoints
        add_to.append(
            Endpoint(
                title=title,
                rule=rule.rule,
                method=calculate_method(rule.methods),
                doc=body,
                module=group.module,
            )
        )

    for func, rule in func_to_rule.items():
        print(
            f"The function {func} is registered as a flask route but has no documentation"
        )


def calculate_method(methods):
    for method in ["GET", "POST", "PUT", "DELETE"]:
        if method in methods:
            return method


def create_endpoint_groups() -> typing.List[Group]:
    groups = [
        Group(flaskapp, [endpoints.docsendpoints]),
        Group(endpoints.systemendpoints),
        Group(endpoints.stopendpoints),
        Group(endpoints.routeendpoints),
        Group(endpoints.tripendpoints),
        Group(endpoints.agencyendpoints),
        Group(endpoints.feedendpoints),
        Group(endpoints.transfersconfigendpoints),
        Group(endpoints.adminendpoints),
    ]
    populate_endpoints(groups)
    return groups


def build_api_index(groups):
    def build_quick_reference_row(endpoint: Endpoint, page: str):
        internal_url = endpoint.title.replace(" ", "-").lower()
        return f"[{endpoint.title}]({page}#{internal_url}) | `{endpoint.method} {endpoint.rule}`"

    lines = [API_INDEX_BASE, "Operation | API endpoint", "----------|-------------"]
    for group in groups:
        lines.append(f"**{group.name()} endpoints**")
        for endpoint in group.all_endpoints():
            lines.append(build_quick_reference_row(endpoint, group.page()[4:]))
    return lines


def build_api_page(group):
    lines = []
    title, doc = clean_doc(group.module.__doc__)
    lines.extend([f"# {title}", "", doc])
    for endpoint in group.all_endpoints():
        lines.extend(
            [
                "",
                f"## {endpoint.title}",
                "",
                f"`{endpoint.method} {endpoint.rule}`",
                "",
                endpoint.doc,
            ]
        )
    return lines


def write_file(lines, location):
    new_content = "\n".join(lines) + "\n"

    try:
        with open(location) as f:
            old_content = f.read()
    except FileNotFoundError:
        old_content = None

    if old_content == new_content:
        print(f"File {location} already up-to-date.")
        return

    print(f"Writing {location}")
    with open(location, "w") as f:
        f.write(new_content)


def main():
    groups = create_endpoint_groups()
    write_file(build_api_index(groups), "docs/docs/api/index.md")
    pages = ["      - api/index.md"]
    for group in groups:
        write_file(build_api_page(group), f"docs/docs/{group.page()}")
        pages.append(f"      - {group.page()}")

    print("\n".join(pages))


if __name__ == "__main__":
    main()
