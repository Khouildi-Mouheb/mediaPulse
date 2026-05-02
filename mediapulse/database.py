from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Utilisation d'une base de données locale SQLite (mediapulse.db)
SQLALCHEMY_DATABASE_URL = "sqlite:///./mediapulse.db"

# "check_same_thread": False est nécessaire uniquement pour SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()