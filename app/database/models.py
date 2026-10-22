
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    services = relationship("Service", back_populates="user")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    apartment = Column(String(150), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    instructions = Column(Text, nullable=True)

    status = Column(
        String(20), default="pendiente", nullable=False
    )
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # Nuevos campos para el cronómetro.
    accumulated_seconds = Column(
        Integer, default=0, nullable=False
    )
    work_started_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="services")
    tasks = relationship(
        "Task",
        back_populates="service",
        cascade="all, delete-orphan",
    )


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(
        Integer, ForeignKey("services.id"), nullable=False, index=True
    )
    name = Column(String(50), nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    service = relationship("Service", back_populates="tasks")
    photo = relationship(
        "Photo",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(
        Integer, ForeignKey("tasks.id"), nullable=False, unique=True
    )
    filename = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)
    size = Column(Integer, nullable=False)
    path = Column(String(500), nullable=False)
    uploaded_at = Column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    task = relationship("Task", back_populates="photo")
