"""
# 로그 정리 서비스
# 오래된 모니터링 로그와 알림을 자동으로 정리합니다.
#
# 주요 기능:
# 1. 오래된 모니터링 로그 삭제
# 2. 오래된 알림 삭제
# 3. 오래된 이메일 로그 삭제
# 4. 통계 요약 후 상세 로그 삭제
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.monitoring import MonitoringAlert, MonitoringLog
from app.models.email_log import EmailLog

logger = logging.getLogger(__name__)


class CleanupService:
    """로그 정리 서비스"""

    # 기본 보관 기간 (일)
    DEFAULT_LOG_RETENTION_DAYS = 30
    DEFAULT_ALERT_RETENTION_DAYS = 90
    DEFAULT_EMAIL_LOG_RETENTION_DAYS = 30

    def __init__(self, db: Session):
        self.db = db

    def cleanup_monitoring_logs(
        self,
        retention_days: int = DEFAULT_LOG_RETENTION_DAYS,
        project_id: Optional[int] = None
    ) -> int:
        """오래된 모니터링 로그 삭제"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        query = self.db.query(MonitoringLog).filter(
            MonitoringLog.created_at < cutoff_date
        )

        if project_id:
            query = query.filter(MonitoringLog.project_id == project_id)

        count = query.count()

        if count > 0:
            query.delete(synchronize_session=False)
            self.db.commit()
            logger.info(f"Deleted {count} monitoring logs older than {retention_days} days")

        return count

    def cleanup_alerts(
        self,
        retention_days: int = DEFAULT_ALERT_RETENTION_DAYS,
        project_id: Optional[int] = None,
        only_resolved: bool = False
    ) -> int:
        """오래된 알림 삭제"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        query = self.db.query(MonitoringAlert).filter(
            MonitoringAlert.created_at < cutoff_date
        )

        if project_id:
            query = query.filter(MonitoringAlert.project_id == project_id)

        if only_resolved:
            query = query.filter(MonitoringAlert.is_resolved.is_(True))

        count = query.count()

        if count > 0:
            query.delete(synchronize_session=False)
            self.db.commit()
            logger.info(f"Deleted {count} alerts older than {retention_days} days")

        return count

    def cleanup_email_logs(
        self,
        retention_days: int = DEFAULT_EMAIL_LOG_RETENTION_DAYS
    ) -> int:
        """오래된 이메일 로그 삭제"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        query = self.db.query(EmailLog).filter(
            EmailLog.created_at < cutoff_date
        )

        count = query.count()

        if count > 0:
            query.delete(synchronize_session=False)
            self.db.commit()
            logger.info(f"Deleted {count} email logs older than {retention_days} days")

        return count

    def cleanup_all(
        self,
        log_retention_days: int = DEFAULT_LOG_RETENTION_DAYS,
        alert_retention_days: int = DEFAULT_ALERT_RETENTION_DAYS,
        email_log_retention_days: int = DEFAULT_EMAIL_LOG_RETENTION_DAYS
    ) -> dict:
        """모든 로그 정리 실행"""
        results = {
            "monitoring_logs_deleted": self.cleanup_monitoring_logs(log_retention_days),
            "alerts_deleted": self.cleanup_alerts(alert_retention_days),
            "email_logs_deleted": self.cleanup_email_logs(email_log_retention_days),
            "cleanup_time": datetime.utcnow().isoformat(),
        }

        logger.info(f"Cleanup completed: {results}")
        return results

    def get_log_statistics(self, project_id: Optional[int] = None) -> dict:
        """로그 통계 조회"""
        # 모니터링 로그 통계
        log_query = self.db.query(MonitoringLog)
        if project_id:
            log_query = log_query.filter(MonitoringLog.project_id == project_id)

        total_logs = log_query.count()

        # 기간별 로그 수
        now = datetime.utcnow()
        logs_7d = log_query.filter(
            MonitoringLog.created_at >= now - timedelta(days=7)
        ).count()
        logs_30d = log_query.filter(
            MonitoringLog.created_at >= now - timedelta(days=30)
        ).count()
        logs_old = log_query.filter(
            MonitoringLog.created_at < now - timedelta(days=30)
        ).count()

        # 알림 통계
        alert_query = self.db.query(MonitoringAlert)
        if project_id:
            alert_query = alert_query.filter(MonitoringAlert.project_id == project_id)

        total_alerts = alert_query.count()
        unresolved_alerts = alert_query.filter(
            MonitoringAlert.is_resolved.is_(False)
        ).count()

        # 이메일 로그 통계
        email_log_count = self.db.query(EmailLog).count()

        return {
            "monitoring_logs": {
                "total": total_logs,
                "last_7_days": logs_7d,
                "last_30_days": logs_30d,
                "older_than_30_days": logs_old,
            },
            "alerts": {
                "total": total_alerts,
                "unresolved": unresolved_alerts,
            },
            "email_logs": {
                "total": email_log_count,
            },
            "statistics_time": datetime.utcnow().isoformat(),
        }

    def get_disk_usage_estimate(self) -> dict:
        """대략적인 디스크 사용량 추정"""
        # 평균 레코드 크기 추정 (bytes)
        AVG_LOG_SIZE = 500
        AVG_ALERT_SIZE = 300
        AVG_EMAIL_LOG_SIZE = 1000

        log_count = self.db.query(MonitoringLog).count()
        alert_count = self.db.query(MonitoringAlert).count()
        email_log_count = self.db.query(EmailLog).count()

        estimated_size = (
            log_count * AVG_LOG_SIZE +
            alert_count * AVG_ALERT_SIZE +
            email_log_count * AVG_EMAIL_LOG_SIZE
        )

        return {
            "monitoring_logs": {
                "count": log_count,
                "estimated_size_bytes": log_count * AVG_LOG_SIZE,
            },
            "alerts": {
                "count": alert_count,
                "estimated_size_bytes": alert_count * AVG_ALERT_SIZE,
            },
            "email_logs": {
                "count": email_log_count,
                "estimated_size_bytes": email_log_count * AVG_EMAIL_LOG_SIZE,
            },
            "total_estimated_size_bytes": estimated_size,
            "total_estimated_size_mb": round(estimated_size / (1024 * 1024), 2),
        }
