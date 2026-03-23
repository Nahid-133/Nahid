"""
Database Utilities (PostgreSQL Configuration)
"""
from models import ServerStatus
import json
from sqlalchemy import create_engine, func,select
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base, Admin, PriceTier, TimeConfig, PaymentMethod, UserDevice
from config import (
    DATABASE_URL,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_START_HOUR,
    DEFAULT_START_MINUTE,
    DEFAULT_END_HOUR,
    DEFAULT_END_MINUTE,
    DEFAULT_PAYMENT_METHODS
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)


SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)


def init_database():
    """Initialize database and create tables"""
    try:
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully (PostgreSQL)")

        session = Session()
        try:
            admin_exists = session.query(Admin).filter_by(username=DEFAULT_ADMIN_USERNAME).first()
            if not admin_exists:
                default_admin = Admin(
                    username=DEFAULT_ADMIN_USERNAME,
                    password=DEFAULT_ADMIN_PASSWORD
                )
                session.add(default_admin)
                print(f"✅ Default admin created: {DEFAULT_ADMIN_USERNAME}")

            time_config_exists = session.query(TimeConfig).filter_by(is_active=True).first()
            if not time_config_exists:
                default_time = TimeConfig(
                    start_hour=DEFAULT_START_HOUR,
                    start_minute=DEFAULT_START_MINUTE,
                    end_hour=DEFAULT_END_HOUR,
                    end_minute=DEFAULT_END_MINUTE,
                    is_active=True
                )
                session.add(default_time)
                print(f"✅ Default time config created: {DEFAULT_START_HOUR}:{DEFAULT_START_MINUTE:02d} - {DEFAULT_END_HOUR}:{DEFAULT_END_MINUTE:02d}")

            for idx, method in enumerate(DEFAULT_PAYMENT_METHODS):
                method_exists = session.query(PaymentMethod).filter_by(method_name=method).first()
                if not method_exists:
                    payment_method = PaymentMethod(
                        method_name=method,
                        is_active=True,
                        display_order=idx
                    )
                    session.add(payment_method)
                    print(f"✅ Default payment method created: {method}")

            session.commit()
            print("✅ Database initialized successfully")

        except Exception as e:
            session.rollback()
            print(f"❌ Error populating database: {e}")
        finally:
            session.close()

    except Exception as e:
        print(f"❌ Error connecting to database (Check URL/SSL): {e}")


def get_db_session():
    """Get a new database session"""
    return Session()


def close_db_session(session):
    """Close database session"""
    session.close()



def get_active_time_config(session):
    """Get active time configuration"""
    return session.query(TimeConfig).filter_by(is_active=True).first()


def get_all_price_tiers(session):
    """Get all price tiers ordered by min_ok"""
    return session.query(PriceTier).order_by(PriceTier.min_ok).all()


def get_active_payment_methods(session):
    """Get all active payment methods"""
    return session.query(PaymentMethod).filter_by(is_active=True).order_by(PaymentMethod.display_order).all()


def verify_admin(session, username, password):
    """Verify admin credentials"""
    admin = session.query(Admin).filter_by(username=username, password=password).first()
    return admin is not None


def update_admin_telegram_id(session, username, telegram_id):
    """Update admin's telegram ID"""
    admin = session.query(Admin).filter_by(username=username).first()
    if admin:
        admin.telegram_id = telegram_id
        session.commit()
        return True
    return False


def is_admin_by_telegram_id(session, telegram_id):
    """Check if telegram ID belongs to an admin"""
    admin = session.query(Admin).filter_by(telegram_id=telegram_id).first()
    return admin is not None

def get_last_server_status(session):
    """Get the last recorded server status"""
    return session.query(ServerStatus).order_by(ServerStatus.id.desc()).first()

def add_server_status(session, status):
    """Add a new server status record"""
    new_record = ServerStatus(status=status)
    session.add(new_record)
    session.commit()
    return new_record


def upsert_user_device(session, telegram_id: int, device_token: str):
    """Insert or update a user's device token"""
    stmt = select(UserDevice).where(UserDevice.telegram_id == telegram_id)
    existing = session.execute(stmt).scalar_one_or_none()

    if existing:
        existing.device_token = device_token
    else:
        new_device = UserDevice(telegram_id=telegram_id, device_token=device_token)
        session.add(new_device)
    session.commit()

def get_user_device_token(session, telegram_id: int):
    """Retrieves the device token for a specific user"""
    stmt = select(UserDevice.device_token).where(UserDevice.telegram_id == telegram_id)
    result = session.execute(stmt).scalar_one_or_none()
    return result

def get_all_device_tokens(session):
    """Retrieve all device tokens for broadcasting"""
    stmt = select(UserDevice.device_token)
    result = session.execute(stmt).scalars().all()
    return result

def is_user_admin(session, telegram_id: int) -> bool:
    """Check if a telegram_id exists in the admins table"""
    stmt = select(Admin).where(Admin.telegram_id == telegram_id)
    admin = session.execute(stmt).scalar_one_or_none()
    return admin is not None