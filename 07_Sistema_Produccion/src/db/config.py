"""
Database Configuration
Multi-tenancy ready con SQLAlchemy
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

# Obtener URL de BD desde .env
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./predicast.db"
)

# Crear engine
# Para SQLite en desarrollo, usar StaticPool para evitar threading issues
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para modelos
Base = declarative_base()


def get_db():
    """
    Dependency para obtener sesión de DB
    Uso en FastAPI: def endpoint(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea todas las tablas"""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Elimina todas las tablas (CUIDADO: solo desarrollo)"""
    Base.metadata.drop_all(bind=engine)
