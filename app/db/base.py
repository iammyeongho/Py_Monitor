from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from app.models.user import User
from app.models.project import Project
from app.models.monitoring import MonitoringLog, MonitoringAlert, MonitoringSetting

# py_monitor 스키마를 사용하도록 MetaData 설정
metadata = MetaData(schema="py_monitor")
Base = declarative_base(metadata=metadata)

