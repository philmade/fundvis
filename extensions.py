from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Define the SQLite database URL
DATABASE_URL = "sqlite:///conflicts.db"

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL)  # Connect to the SQLite database

# Create a session factory
session_factory = sessionmaker(bind=engine)

# Create all tables in the database
# This will create the tables defined in models.py if they don't already exist
Base.metadata.create_all(engine)
