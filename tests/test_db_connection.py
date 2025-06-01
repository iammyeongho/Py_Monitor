import pytest
from sqlalchemy import text
from app.db.session import SessionLocal

def test_database_connection():
    """데이터베이스 연결 및 스키마 설정을 테스트합니다."""
    db = SessionLocal()
    try:
        # 1. 연결 테스트
        result = db.execute(text("SELECT 1"))
        assert result.scalar() == 1, "데이터베이스 연결 실패"
        
        # 2. 스키마 존재 확인
        result = db.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'py_monitor'"))
        assert result.scalar() is not None, "py_monitor 스키마가 존재하지 않음"
        
        # 3. 스키마 권한 확인
        result = db.execute(text("SELECT has_schema_privilege(current_user, 'py_monitor', 'USAGE')"))
        assert result.scalar() is True, "py_monitor 스키마에 대한 권한이 없음"
        
        print("✅ 데이터베이스 연결 및 스키마 설정이 정상입니다.")
        
    except Exception as e:
        pytest.fail(f"데이터베이스 테스트 실패: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    test_database_connection() 