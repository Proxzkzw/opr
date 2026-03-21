from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import hashlib
import os

# Uses DATABASE_URL env var if set (PostgreSQL on Railway),
# otherwise falls back to local SQLite for development.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./fleet.db")

# SQLite needs check_same_thread=False; PostgreSQL doesn't use that arg
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Railway provides postgres:// but SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine)
Base         = declarative_base()


class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True)
    username   = Column(String, unique=True, nullable=False)
    password   = Column(String, nullable=False)
    role       = Column(String, nullable=False)          # "admin" | "driver"
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    vehicle    = relationship("Vehicle", back_populates="driver")


class Vehicle(Base):
    __tablename__ = "vehicles"
    id     = Column(Integer, primary_key=True)
    name   = Column(String, nullable=False)
    color  = Column(String, default="#6C8AFF")
    driver = relationship("User", back_populates="vehicle", uselist=False)
    routes = relationship("Route", back_populates="vehicle", cascade="all, delete")


class Warehouse(Base):
    __tablename__ = "warehouses"
    id     = Column(Integer, primary_key=True)
    name   = Column(String, nullable=False)
    lat    = Column(Float,  nullable=False)
    lon    = Column(Float,  nullable=False)
    routes = relationship("Route", back_populates="warehouse")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "lat": self.lat, "lon": self.lon}


class Route(Base):
    __tablename__ = "routes"
    id           = Column(Integer, primary_key=True)
    name         = Column(String, nullable=False)
    vehicle_id   = Column(Integer, ForeignKey("vehicles.id"),   nullable=True)
    driver_id    = Column(Integer, ForeignKey("users.id"),      nullable=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    status       = Column(String, default="draft")
    created_at   = Column(DateTime, default=datetime.utcnow)
    order        = Column(String, default="")
    vehicle      = relationship("Vehicle", back_populates="routes")
    driver       = relationship("User", foreign_keys=[driver_id])
    warehouse    = relationship("Warehouse", back_populates="routes")
    stops        = relationship("Stop", back_populates="route",
                                cascade="all, delete", order_by="Stop.id")


class Stop(Base):
    __tablename__ = "stops"
    id              = Column(Integer, primary_key=True)
    route_id        = Column(Integer, ForeignKey("routes.id"),   nullable=True)
    vehicle_id      = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    lat             = Column(Float)
    lon             = Column(Float)
    name            = Column(String)
    recipient_name  = Column(String, default="")
    recipient_phone = Column(String, default="")
    recipient_note  = Column(Text,   default="")
    status          = Column(String, default="pending")
    status_message  = Column(Text,   default="")
    updated_at      = Column(DateTime, default=datetime.utcnow)
    route           = relationship("Route", back_populates="stops")


class Setting(Base):
    __tablename__ = "settings"
    key   = Column(String, primary_key=True)
    value = Column(String)


class Notification(Base):
    __tablename__ = "notifications"
    id         = Column(Integer, primary_key=True)
    message    = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read    = Column(Boolean, default=False)
    tag        = Column(String, default="")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def get_db():
    return SessionLocal()


def get_setting(db, key: str, default=None):
    row = db.query(Setting).filter(Setting.key == key).first()
    return row.value if row else default


def set_setting(db, key: str, value: str):
    row = db.query(Setting).filter(Setting.key == key).first()
    if row:
        row.value = value
    else:
        db.add(Setting(key=key, value=value))
    db.commit()


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if not db.query(User).filter(User.role == "admin").first():
        db.add(User(username="admin", password=hash_password("admin123"), role="admin"))
        db.commit()
    db.close()


init_db()
