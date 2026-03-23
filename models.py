"""
Database Models (PostgreSQL Fixed)
"""
from sqlalchemy import Column, BigInteger, String, Date, Float, Boolean, DateTime, Text, func , Integer
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class Admin(Base):
    """Admin authentication table"""
    __tablename__ = 'admins'

    id = Column(BigInteger, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    telegram_id = Column(BigInteger, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserAccount(Base):
    """User submitted accounts table"""
    __tablename__ = 'user_accounts'

    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    entry_date = Column(Date, nullable=False)
    sender_id = Column(BigInteger, nullable=False)
    telegram_username = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AdminAccount(Base):
    """Admin verified accounts (for conflicts and final reports)"""
    __tablename__ = 'admin_accounts'

    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    entry_date = Column(Date, nullable=False)
    sender_id = Column(BigInteger)
    telegram_username = Column(String)
    ok_status = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserPayment(Base):
    """User payment information table"""
    __tablename__ = 'user_payments'

    id = Column(BigInteger, primary_key=True)
    sender_id = Column(BigInteger, nullable=False)
    telegram_username = Column(String)
    entry_date = Column(Date, nullable=False)
    payment_data = Column(Text)
    paid_status = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PriceTier(Base):
    """Price configuration table"""
    __tablename__ = 'price_tiers'

    id = Column(BigInteger, primary_key=True)
    min_ok = Column(Integer, nullable=False)
    max_ok = Column(Integer, nullable=False)
    price_per_ok = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TimeConfig(Base):
    """Time window configuration table"""
    __tablename__ = 'time_configs'

    id = Column(BigInteger, primary_key=True)
    start_hour = Column(Integer, nullable=False)
    start_minute = Column(Integer, nullable=False)
    end_hour = Column(Integer, nullable=False)
    end_minute = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ServerStatus(Base):
    """Server monitoring status table"""
    __tablename__ = 'server_status'

    id = Column(Integer, primary_key=True)
    status = Column(String(10), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class PaymentMethod(Base):
    """Dynamic payment methods table"""
    __tablename__ = 'payment_methods'

    id = Column(BigInteger, primary_key=True)
    method_name = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class UserDevice(Base):
    """User device tokens for FCM notifications"""
    __tablename__ = 'user_devices'

    id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    device_token = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))