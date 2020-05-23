from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from transiter import parse
from .base import Base


class AlertMessage(Base):
    __tablename__ = "alert_message"

    pk = Column(Integer, primary_key=True)
    alert_pk = Column(Integer, ForeignKey("alert.pk"), index=True, nullable=False)

    header = Column(String, nullable=False)
    description = Column(String, nullable=False)
    url = Column(String)
    language = Column(String)

    alert = relationship("Alert", back_populates="messages", cascade="none")

    @staticmethod
    def from_parsed_message(message: parse.AlertMessage) -> "AlertMessage":
        return AlertMessage(
            header=message.header,
            description=message.description,
            url=message.url,
            language=message.language,
        )
