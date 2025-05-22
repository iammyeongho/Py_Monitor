from sqlalchemy.ext.declarative import declarative_base
from app.models.user import User
from app.models.project import Project
from app.models.monitoring import MonitoringLog, MonitoringAlert, MonitoringSetting

Base = declarative_base()

