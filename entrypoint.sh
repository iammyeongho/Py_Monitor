#!/bin/bash
# =============================================================================
# PyMonitor Docker Entrypoint
# =============================================================================
# 컨테이너 시작 시 실행되는 초기화 스크립트
#
# 실행 순서:
# 1. PostgreSQL 연결 대기
# 2. py_monitor 스키마 생성 (없는 경우)
# 3. Alembic 마이그레이션 실행
# 4. Uvicorn으로 FastAPI 앱 시작
# =============================================================================

set -e

echo "=== PyMonitor Entrypoint ==="

# ---------------------------------------------------------------------------
# 1. PostgreSQL 연결 대기
# ---------------------------------------------------------------------------
# pg_isready: PostgreSQL 클라이언트 도구 (Dockerfile에서 postgresql-client 설치)
# Docker Compose의 depends_on + healthcheck로도 대기하지만,
# 네트워크 지연 등을 고려한 추가 안전장치
echo "PostgreSQL 연결 대기 중 (${POSTGRES_SERVER}:${POSTGRES_PORT:-5432})..."
MAX_RETRIES=30
RETRY_COUNT=0
until pg_isready -h "${POSTGRES_SERVER}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-postgres}" -q; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: PostgreSQL ${MAX_RETRIES}회 재시도 후에도 연결 실패. 종료합니다."
        exit 1
    fi
    echo "  대기 중... (${RETRY_COUNT}/${MAX_RETRIES})"
    sleep 2
done
echo "PostgreSQL 연결 성공."

# ---------------------------------------------------------------------------
# 2. py_monitor 스키마 생성
# ---------------------------------------------------------------------------
# 모델이 py_monitor 스키마를 참조할 수 있으므로 미리 생성
# 이미 존재하면 무시 (IF NOT EXISTS)
echo "py_monitor 스키마 확인 중..."
PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h "${POSTGRES_SERVER}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-postgres}" \
    -d "${POSTGRES_DB:-py_monitor}" \
    -c "CREATE SCHEMA IF NOT EXISTS py_monitor;" \
    2>/dev/null && echo "py_monitor 스키마 준비 완료." \
    || echo "  스키마 생성 건너뜀 (이미 존재하거나 권한 부족)"

# ---------------------------------------------------------------------------
# 3. Alembic 마이그레이션 실행
# ---------------------------------------------------------------------------
# 테이블 생성 및 스키마 변경 사항 적용
# 이미 최신 상태이면 아무 작업도 하지 않음
echo "Alembic 마이그레이션 실행 중..."
alembic upgrade head
echo "마이그레이션 완료."

# ---------------------------------------------------------------------------
# 4. 애플리케이션 시작
# ---------------------------------------------------------------------------
# exec: 현재 셸 프로세스를 uvicorn으로 교체
# Docker의 SIGTERM 시그널이 uvicorn에 직접 전달됨 (graceful shutdown)
echo "Uvicorn 시작..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
