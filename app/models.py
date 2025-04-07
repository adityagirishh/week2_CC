from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./database/database.db"  # SQLite for simplicity

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Function(Base):
    __tablename__ = "functions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    route = Column(String, unique=True)
    language = Column(String)  # "python" or "javascript"
    code = Column(Text)
    timeout = Column(Integer)  # in seconds
