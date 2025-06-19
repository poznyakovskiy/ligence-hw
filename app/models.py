from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import CheckConstraint

from .database import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    modifications = relationship("Modification", back_populates="image")

class Modification(Base):
    __tablename__ = "modifications"

    image_id = Column(String, ForeignKey("images.id"), primary_key=True)
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    modification_type = Column(String, nullable=False)
    params = Column(JSON, nullable=False)
    verification = Column(String, nullable=False, default="pending")
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "verification IN ('pending', 'successful', 'failed')",
            name="check_verification_values"
        ),
    )

    image = relationship("Image", back_populates="modifications")