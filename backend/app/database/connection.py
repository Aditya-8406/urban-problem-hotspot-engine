import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/urban_hotspot",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
