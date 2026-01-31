# PyMonitor 기능 구현 진행현황

## 1순위 - 핵심 기능

| # | 기능 | 상태 | 비고 |
|---|------|------|------|
| 1.1 | 성능 임계값 알림 | 완료 | 응답시간 초과 시 자동 알림 |
| 1.2 | SSL/도메인 만료 알림 | 완료 | D-day 기반 자동 알림 |
| 1.3 | 이메일 알림 연동 | 완료 | SMTP 실제 발송 |
| 1.4 | Slack/Discord 웹훅 | 완료 | 장애 시 즉시 알림 |
| 1.5 | 실시간 WebSocket | 완료 | 대시보드 실시간 업데이트 |

## 2순위 - 사용성 개선

| # | 기능 | 상태 | 비고 |
|---|------|------|------|
| 2.1 | 대시보드 통계 카드 | 완료 | 전체 가용률, 평균 응답시간 |
| 2.2 | 프로젝트 그룹핑 | 완료 | 카테고리/태그 분류 |
| 2.3 | 다크모드 | 완료 | 테마 전환 (풀스택) |
| 2.4 | CSV/PDF 리포트 | 완료 | 데이터 내보내기 |
| 2.5 | 모바일 반응형 개선 | 완료 | 태블릿/모바일 최적화 (백엔드) |

## 3순위 - 고급 기능

| # | 기능 | 상태 | 비고 |
|---|------|------|------|
| 3.1 | 다중 사용자 권한 | 대기 | 팀원 초대, 역할 기반 |
| 3.2 | API Rate Limiting | 대기 | 요청 제한 |
| 3.3 | Redis 캐싱 | 대기 | 응답 속도 개선 |
| 3.4 | 공개 상태 페이지 | 대기 | 외부 공유용 |
| 3.5 | Uptime 배지 | 대기 | README용 상태 배지 |

---

## 작업 로그

### 2026-01-28

- 2.1 대시보드 통계 카드 구현 완료
  - DashboardStats 모델 추가
  - `/charts/stats` 엔드포인트 추가
  - 전체 프로젝트 수, 가용성, 응답시간, 알림 통계 제공
- 2.2 프로젝트 그룹핑 구현 완료
  - Project 모델에 category, tags 필드 추가
  - `/projects` 엔드포인트에 category, tag 필터링 추가
  - `/projects/categories` 카테고리 목록 조회 엔드포인트 추가
  - `/projects/tags` 태그 목록 조회 엔드포인트 추가
  - DB 마이그레이션 적용 완료
- 2.3 다크모드 백엔드 구현 완료
  - User 모델에 theme, language, timezone 필드 추가
  - UserSettings, UserSettingsUpdate 스키마 추가
  - `/auth/me/settings` GET/PUT 엔드포인트 추가
  - DB 마이그레이션 적용 완료
- 2.4 CSV/PDF 리포트 구현 완료
  - ReportService: 리포트 데이터 생성, CSV/PDF 내보내기
  - `/reports` GET: 리포트 데이터 조회
  - `/reports/export/csv` GET: CSV 다운로드
  - `/reports/export/pdf` GET: PDF용 HTML 반환
- 2.5 모바일 반응형 개선 백엔드 구현 완료
  - PaginatedResponse, MobileProjectSummary 스키마 추가
  - `/mobile/projects` GET: 페이지네이션된 프로젝트 목록
  - `/mobile/dashboard` GET: 간소화된 대시보드 요약
  - `/mobile/alerts` GET: 페이지네이션된 알림 목록
- 에러 수정
  - PlaywrightMonitorService 초기화 오류 수정 (db 인자 누락)
- 다크모드 프론트엔드 구현 완료
  - theme.js 테마 관리 컴포넌트 추가
  - CSS 변수 다크모드 대응 (semantic color variables)
  - 서버 동기화 (theme 설정 저장/로드)
- 다크모드 UI 개선
  - 테마 토글 버튼을 헤더에서 우측 하단 플로팅 버튼으로 변경
  - 이모지(🌙/☀️) 대신 SVG 아이콘 사용
  - 전체 CSS 파일 semantic color 변수로 업데이트
    - _auth.css, _forms.css, _buttons.css, _modals.css
    - _dashboard.css, _tools.css, _loading.css, _cards.css, _header.css
    - _tabs.css, _badges.css, _container.css, _toast.css
  - 모든 HTML 페이지에 theme.js 포함 (login, register 포함)
- 전체 검증 완료
  - PlaywrightMonitorService.close() 메서드 추가 (테스트 teardown 오류 수정)
  - 앱 로드 성공 (75개 라우트)
  - 테스트 통과: 41 passed, 8 skipped, 0 errors

- 진행현황 파일 생성
- 1.1 성능 임계값 알림 구현 완료
  - scheduler.py에 `_handle_performance_alert` 메서드 추가
  - project.time_limit 초과 시 알림 생성
  - time_limit_interval 간격으로 중복 알림 방지
- 1.2 SSL/도메인 만료 알림 구현 완료
  - `_ssl_expiry_check_loop`: 24시간마다 모든 프로젝트 체크
  - `_check_ssl_expiry`: SSL 인증서 만료 체크
  - `_check_domain_expiry`: 도메인 만료 체크
  - D-30, D-14, D-7, D-3, D-1 알림 발송
- 1.3 이메일 알림 연동 (기존 구현 확장)
  - 성능 경고, SSL, 도메인 알림 템플릿 추가
  - `_create_performance_email_body`, `_create_ssl_email_body`, `_create_domain_email_body`
- 1.4 Slack/Discord 웹훅 (기존 구현 확장)
  - 새 알림 유형별 색상/이모지 매핑 추가
- 1.5 실시간 WebSocket 구현 완료
  - app/api/v1/endpoints/websocket.py 생성
  - ConnectionManager: 연결 관리, 프로젝트 구독
  - 모니터링 결과 실시간 푸시
  - 스케줄러와 연동
