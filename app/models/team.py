"""팀 및 팀원 모델"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base_class import Base


class TeamRole(str, enum.Enum):
    """팀원 역할"""
    OWNER = "owner"      # 소유자 - 모든 권한
    ADMIN = "admin"      # 관리자 - 팀원 관리, 프로젝트 관리
    MEMBER = "member"    # 멤버 - 읽기/쓰기
    VIEWER = "viewer"    # 뷰어 - 읽기만


class Team(Base):
    """팀 모델"""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    projects = relationship("TeamProject", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    """팀 멤버 모델"""

    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), default=TeamRole.MEMBER.value)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    invited_at = Column(DateTime(timezone=True), default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    # 유니크 제약조건: 같은 팀에 같은 사용자는 한 번만
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_member"),
    )

    # 관계 설정
    team = relationship("Team", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])

    # ==================== 비즈니스 메서드 ====================

    @property
    def is_owner(self) -> bool:
        """소유자 여부"""
        return self.role == TeamRole.OWNER.value

    @property
    def is_admin(self) -> bool:
        """관리자 여부"""
        return self.role in [TeamRole.OWNER.value, TeamRole.ADMIN.value]

    @property
    def can_write(self) -> bool:
        """쓰기 권한 여부"""
        return self.role in [TeamRole.OWNER.value, TeamRole.ADMIN.value, TeamRole.MEMBER.value]

    @property
    def can_manage_members(self) -> bool:
        """팀원 관리 권한 여부"""
        return self.is_admin


class TeamProject(Base):
    """팀 프로젝트 연결 모델"""

    __tablename__ = "team_projects"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    added_at = Column(DateTime(timezone=True), default=func.now())

    # 유니크 제약조건
    __table_args__ = (
        UniqueConstraint("team_id", "project_id", name="uq_team_project"),
    )

    # 관계 설정
    team = relationship("Team", back_populates="projects")
    project = relationship("Project")
    added_by_user = relationship("User", foreign_keys=[added_by])


class TeamInvitation(Base):
    """팀 초대 모델"""

    __tablename__ = "team_invitations"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(20), default=TeamRole.MEMBER.value)
    token = Column(String(100), unique=True, nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    # 관계 설정
    team = relationship("Team")
    inviter = relationship("User", foreign_keys=[invited_by])
