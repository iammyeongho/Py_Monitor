from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

# py_monitor 스키마를 사용하도록 MetaData 설정
metadata = MetaData(schema="py_monitor")
Base = declarative_base(metadata=metadata)
