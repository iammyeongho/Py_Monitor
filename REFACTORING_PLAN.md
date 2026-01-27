# PyMonitor 리팩토링 계획

## 현재 문제점

### 프론트엔드
1. **CSS (2513줄)**: 단일 파일에 모든 스타일 포함
2. **HTML**: JavaScript 코드가 인라인으로 포함 (index.html 1566줄)
3. **JS**: 페이지별 로직이 분리되지 않음

### 백엔드
1. **monitoring.py (1033줄)**: API 엔드포인트가 너무 많이 집중됨
2. **서비스 계층**: 일부 비즈니스 로직이 API 레이어에 혼재

---

## 리팩토링 계획

### Phase 1: CSS 모듈화

```
frontend/style/
├── base/
│   ├── _reset.css          # CSS Reset
│   ├── _variables.css      # CSS Variables (색상, 폰트, 간격)
│   └── _typography.css     # 타이포그래피
├── components/
│   ├── _buttons.css        # 버튼 스타일
│   ├── _cards.css          # 카드 컴포넌트
│   ├── _forms.css          # 폼 요소
│   ├── _modals.css         # 모달
│   ├── _tables.css         # 테이블
│   ├── _badges.css         # 뱃지, 상태 표시
│   ├── _charts.css         # 차트 관련
│   └── _toast.css          # 토스트 알림
├── layout/
│   ├── _header.css         # 헤더/네비게이션
│   ├── _grid.css           # 그리드 시스템
│   └── _container.css      # 컨테이너
├── pages/
│   ├── _dashboard.css      # 대시보드 전용
│   ├── _auth.css           # 로그인/회원가입
│   ├── _project.css        # 프로젝트 페이지
│   └── _tools.css          # 도구 페이지
├── utilities/
│   └── _utilities.css      # 유틸리티 클래스
└── style.css               # 메인 (import만)
```

### Phase 2: JavaScript 모듈화

```
frontend/js/
├── core/
│   ├── api.js              # API 호출 래퍼
│   ├── auth.js             # 인증 관리 (기존)
│   └── utils.js            # 유틸리티 함수
├── components/
│   ├── toast.js            # 토스트 알림
│   ├── modal.js            # 모달 관리
│   ├── chart.js            # 차트 관련
│   └── scheduler.js        # 스케줄러 컨트롤
├── pages/
│   ├── dashboard.js        # 대시보드 로직
│   ├── project.js          # 프로젝트 페이지 (기존)
│   └── tools.js            # 도구 페이지
└── monitoring.js           # 모니터링 API (기존)
```

### Phase 3: 백엔드 API 분리

```
app/api/v1/endpoints/
├── monitoring/
│   ├── __init__.py
│   ├── status.py           # 상태 조회 API
│   ├── settings.py         # 설정 API
│   ├── logs.py             # 로그 API
│   ├── alerts.py           # 알림 API
│   ├── scheduler.py        # 스케줄러 API
│   ├── cleanup.py          # 정리 API
│   └── charts.py           # 차트 데이터 API
├── projects.py
├── users.py
└── notifications.py
```

### Phase 4: 백엔드 클린 아키텍처 검토

현재 구조:
```
app/
├── api/          # Presentation Layer (Controller)
├── schemas/      # DTO Layer
├── services/     # Business Logic Layer
├── models/       # Domain/Entity Layer
├── db/           # Infrastructure Layer (DB)
├── core/         # Configuration
└── utils/        # Utilities
```

#### 아키텍처 분석 결과 (2024-01 검토)

**전체 점수: 7.2/10**

| 계층 | 점수 | 평가 |
|-----|------|------|
| Presentation (API) | 6/10 | API에서 직접 DB 쿼리 수행 |
| Application (Services) | 7/10 | Repository 패턴 부재 |
| Domain (Models) | 8/10 | 도메인 메서드 부족 |
| DTO (Schemas) | 8/10 | 잘 구현됨 |
| Infrastructure | 7/10 | 관심사 분산 |
| Configuration | 9/10 | 우수 |

#### 발견된 문제점

1. **API 계층에서 직접 DB 접근** (52개 쿼리)
   - Service 계층을 우회하는 패턴

2. **Repository 패턴 부재**
   - 데이터 접근 로직이 Service에 산재

3. **알림 로직 중복**
   - utils/notifications.py와 services/notification_service.py 중복

#### 개선 권장사항 (우선순위별)

**1순위 (즉시 개선 필요)** - 완료
- [x] Repository 패턴 도입 (app/repositories/)
- [x] 커스텀 예외 클래스 정의 (app/core/exceptions/)
- [x] 알림 로직 통합

**2순위 (중기 개선)**
- [ ] Repository 인터페이스 추상화 (ABC)
- [ ] 도메인 모델에 비즈니스 메서드 추가
- [ ] Infrastructure 계층 정리

**3순위 (장기 개선)**
- [ ] 의존성 주입 강화
- [ ] 캐싱 전략 도입 (Redis)

---

## 실행 순서

1. **CSS 분리** - 완료
2. **JavaScript 분리** - 완료
3. **백엔드 API 분리** - 완료
4. **아키텍처 개선** - 완료

---

## 완료된 작업

### Phase 1: CSS 모듈화 - 완료
- 17개 CSS 모듈 파일로 분리
- main.css에서 @import로 통합
- 모든 HTML 파일 업데이트

### Phase 2: JavaScript 모듈화 - 완료
- core/utils.js: 공통 유틸리티
- components/toast.js, modal.js, scheduler.js, chart.js
- pages/dashboard.js
- index.html 인라인 JS 1160줄 -> 외부 모듈로 분리

### Phase 3: 백엔드 API 분리 - 완료
- monitoring.py (1034줄) -> 9개 모듈로 분리
- status.py, settings.py, ssl.py, checks.py, logs.py
- alerts.py, scheduler.py, cleanup.py, charts.py

### Phase 4: 아키텍처 검토 - 완료
- 6계층 구조 분석 완료
- 개선 로드맵 작성
- 현재 구조는 양호 (7.2/10)

### Phase 5: 클린 아키텍처 적용 - 완료
- **Repository 패턴 도입**
  - app/repositories/base.py: BaseRepository 추상 클래스
  - app/repositories/user_repository.py: 사용자 데이터 접근
  - app/repositories/project_repository.py: 프로젝트 데이터 접근
  - app/repositories/monitoring_repository.py: 모니터링 데이터 접근
  - app/repositories/notification_repository.py: 알림 데이터 접근
- **Service 계층 리팩토링**
  - Repository를 통한 데이터 접근
  - 비즈니스 로직과 데이터 접근 분리
- **커스텀 예외 클래스**
  - app/core/exceptions/base.py: 예외 클래스 정의
  - app/core/exceptions/handlers.py: 전역 예외 핸들러
  - NotFoundError, ValidationError, AuthenticationError, ConflictError
- **알림 로직 통합**
  - services/notification_service.py로 통합
  - utils/notifications.py는 템플릿만 유지

---

## 주의사항

- 각 단계별 커밋
- 기능 테스트 후 다음 단계 진행
- 기존 URL/API 경로 유지 (하위 호환성)
