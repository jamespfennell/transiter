from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from transiter import parse
from .base import Base
from .updatableentity import updatable_from


@updatable_from(parse.Agency)
class Agency(Base):
    __tablename__ = "agency"

    pk = Column(Integer, primary_key=True)
    id = Column(String, nullable=False)
    system_pk = Column(Integer, ForeignKey("system.pk"), nullable=False)
    source_pk = Column(
        Integer, ForeignKey("feed_update.pk"), index=True, nullable=False
    )

    name = Column(String, nullable=False)
    url = Column(String)
    timezone = Column(String, nullable=False)
    language = Column(String)
    phone = Column(String)
    fare_url = Column(String)
    email = Column(String)

    system = relationship("System", back_populates="agencies")
    source = relationship("FeedUpdate", cascade="none")
    routes = relationship("Route", back_populates="agency", cascade="none")
    alerts = relationship(
        "Alert", secondary="alert_agency", back_populates="agencies", cascade="none"
    )

    __table_args__ = (UniqueConstraint("system_pk", "id"),)

    @staticmethod
    def from_parsed_agency(agency: parse.Agency) -> "Agency":
        return Agency(
            id=agency.id,
            name=agency.name,
            timezone=agency.timezone,
            language=agency.language,
            phone=agency.phone,
            fare_url=agency.fare_url,
            email=agency.email,
        )
