from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.base_class import Base

class InternalLog(Base):
    __tablename__ = "internal_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_type = Column(String(50), nullable=False)
    message = Column(String(1024), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
