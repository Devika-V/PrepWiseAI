from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# This is the address of your SQLite database file.
# "sqlite:///./prepwise.db" means: create/use a file called prepwise.db
# in the same folder this code runs from.
SQLALCHEMY_DATABASE_URL = "sqlite:///./prepwise.db"

# check_same_thread=False is a SQLite-specific setting needed because
# FastAPI can handle a single request across multiple threads, but SQLite
# normally only allows the thread that opened a connection to use it.
# This setting safely relaxes that for our use case.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal is a factory that creates new database "conversations" (sessions).
# Every API request that touches the database will create one of these,
# use it, then close it.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class every one of our table models (in models.py)
# will inherit from. It's what lets SQLAlchemy turn Python classes into
# real database tables.
Base = declarative_base()


def get_db():
    """
    A FastAPI 'dependency' - every route that needs database access will
    request this function. It opens a session, hands it to the route,
    and guarantees the session is closed afterward even if the route
    raises an error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
