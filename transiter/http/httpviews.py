import dataclasses

from transiter.services import views


@dataclasses.dataclass
class SystemsInstalled(views.View):
    count: int


@dataclasses.dataclass
class InternalDocumentationLink(views.View):
    pass


@dataclasses.dataclass
class ExternalDocumentationLink(views.View):
    href: str = "https://docs.transiter.io"
