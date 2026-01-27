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

개선 방향:
- Repository 패턴 도입 검토 (services와 models 사이)
- 서비스 간 의존성 명확화
- 인터페이스/추상 클래스 도입 검토

---

## 실행 순서

1. **CSS 분리** (충돌 위험 낮음)
2. **JavaScript 분리** (의존성 주의)
3. **백엔드 API 분리** (테스트 필수)
4. **아키텍처 개선** (점진적)

---

## 주의사항

- 각 단계별 커밋
- 기능 테스트 후 다음 단계 진행
- 기존 URL/API 경로 유지 (하위 호환성)
