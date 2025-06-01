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

from sqlalchemy import Boolean, Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    """
    # Laravel의 User 모델과 유사한 역할
    # 
    # 주요 필드:
    # - id: 기본 키 (Laravel의 $primaryKey)
    # - email: 사용자 이메일 (unique 제약조건)
    # - password_hash: 해시된 비밀번호
    # - status: 계정 상태 (active/inactive)
    # - last_login_at: 마지막 로그인 시간
    # - last_login_ip: 마지막 로그인 IP
    # - created_at, updated_at: Laravel의 timestamps와 동일
    # - deleted_at: 소프트 삭제를 위한 필드 (Laravel의 softDeletes)
    """
    __tablename__ = "users"  # Laravel의 protected $table = 'users'

    id = Column(Integer, primary_key=True, index=True)  # Laravel의 $primaryKey
    email = Column(String(255), unique=True, nullable=False)  # unique() 제약조건
    password_hash = Column(String(255), nullable=False)  # 비밀번호 해시 저장
    status = Column(Boolean, default=True)  # 계정 활성화 상태
    last_login_at = Column(DateTime, default=func.now())  # 마지막 로그인 시간
    last_login_ip = Column(String(45))  # IPv6 대응
    created_at = Column(DateTime, default=func.now())  # Laravel의 $timestamps
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 자동 업데이트
    deleted_at = Column(DateTime, nullable=True)  # Laravel의 softDeletes

    # 관계 설정 (Laravel의 hasMany와 유사)
    # cascade="all, delete-orphan"은 Laravel의 onDelete('cascade')와 유사
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
