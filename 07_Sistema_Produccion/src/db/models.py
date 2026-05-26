"""
Database Models con SQLAlchemy
Multi-tenancy ready: cada modelo tiene tenant_id
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.db.config import Base


class Tenant(Base):
    """Modelo para empresas/tenants"""
    __tablename__ = "tenants"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(String(1000), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant {self.name}>"


class User(Base):
    """Modelo para usuarios - Multi-tenancy ready"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    tenant = relationship("Tenant", back_populates="users")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    
    # Índice compuesto para email por tenant (no duplicar email dentro misma empresa)
    __table_args__ = (Index('idx_tenant_email', 'tenant_id', 'email', unique=True),)
    
    def __repr__(self):
        return f"<User {self.email}@{self.tenant_id}>"


class Prediction(Base):
    """Modelo para predicciones - Multi-tenancy ready"""
    __tablename__ = "predictions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Features del input
    stock_anterior = Column(Integer, nullable=False)
    stock_posterior = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    año = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    trimestre = Column(Integer, nullable=False)
    dia_semana = Column(Integer, nullable=False)
    canal_promedio_demanda = Column(Float, nullable=True)
    campana_promedio_demanda = Column(Float, nullable=True)
    cliente_promedio_demanda = Column(Float, nullable=True)
    producto_promedio_demanda = Column(Float, nullable=True)
    canal_venta_encoded = Column(Integer, nullable=False)
    campana_encoded = Column(Integer, nullable=False)
    empresa_cliente_encoded = Column(Integer, nullable=False)
    producto_codigo_encoded = Column(Integer, nullable=False)
    
    # Resultado de predicción
    predicted_quantity = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    tenant = relationship("Tenant", back_populates="predictions")
    user = relationship("User", back_populates="predictions")
    
    # Índices para queries rápidas
    __table_args__ = (
        Index('idx_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_tenant_user', 'tenant_id', 'user_id'),
    )
    
    def __repr__(self):
        return f"<Prediction {self.id}: {self.predicted_quantity:.2f}>"


class ModelMetadata(Base):
    """Almacenar metadata de versiones de modelos"""
    __tablename__ = "model_metadata"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(String(50), nullable=False, unique=True, index=True)
    r2_score = Column(Float, nullable=False)
    mae = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    n_features = Column(Integer, nullable=False)
    features = Column(String(2000), nullable=False)  # JSON string
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ModelMetadata {self.version}: R²={self.r2_score:.4f}>"
