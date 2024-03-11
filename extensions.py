from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from models import Base
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)  # Replace with your database connection URL
session_factory = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
