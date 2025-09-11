import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv
from sqlalchemy import create_engine
from utils_secrets import get_secret

# db.py
from sqlalchemy import create_engine
from utils_secrets import get_secret

def get_engine():
    host = get_secret("DB_HOST")
    user = get_secret("DB_USER")
    pwd  = get_secret("DB_PASSWORD")
    db   = get_secret("DB_NAME")

    # Se estiver usando MySQL
    url = f"mysql+pymysql://{user}:{pwd}@{host}/{db}"
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)

def get_engine():
    host = os.getenv("DB_HOST")
    port = int(os.getenv("DB_PORT", "3306"))
    db   = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    pwd  = os.getenv("DB_PASS")
    charset = os.getenv("DB_CHARSET", "utf8mb4")

    if not db:
        raise RuntimeError("DB_NAME não definido no .env (MySQL exige database).")

    url = URL.create(
        drivername="mysql+pymysql",
        username=user,
        password=pwd,
        host=host,
        port=port,
        database=db,
        query={"charset": charset}
    )
    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=5,
        max_overflow=10,
        echo=False,
        future=True,
    )
    return engine
