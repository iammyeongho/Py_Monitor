"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 User 모델과 유사한 역할을 합니다.
# SQLAlchemy ORM을 사용하여 users 테이블을 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. __tablename__ = "users"  # Laravel의 protected $table = 'users'와 동일
# 2. Column() = Laravel의 $fillable과 유사하지만, 타입과 제약조건을 직접 지정
# 3. relationship() = Laravel의 hasMany(), belongsTo()와 유사
# 4. func.now() = Laravel의 now()와 유사
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class User(Base):
    """사용자 모델"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    profile_image = Column(String(255), nullable=True)  # 프로필 이미지 URL
    phone = Column(String(20), nullable=True)  # 연락처
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    email_notifications = Column(Boolean, default=True)  # 이메일 알림 설정
    last_login_at = Column(DateTime(timezone=True), nullable=True)  # 마지막 로그인 시간
    created_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # soft delete

    # 관계 설정 (Laravel의 hasMany와 유사)
    # cascade="all, delete-orphan"은 Laravel의 onDelete('cascade')와 유사
    projects = relationship(
        "Project", back_populates="user", cascade="all, delete-orphan"
    )
    email_logs = relationship(
        "EmailLog", back_populates="user", cascade="all, delete-orphan"
    )
