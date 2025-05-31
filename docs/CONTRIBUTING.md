# Contributing Guide (기여 가이드)

이 문서는 본 프로젝트에 기여하는 모든 개발자를 위한 협업 규칙 및 개발 가이드입니다.

---

## 1. 브랜치 전략
- **main**: 운영 배포용(프로덕션) 브랜치
- **develop**: 개발 통합 브랜치
- **feature/**: 기능 개발용 브랜치 (ex: `feature/monitoring-api`)
- **fix/**: 버그 수정 브랜치 (ex: `fix/login-bug`)
- **hotfix/**: 운영 긴급 수정 (ex: `hotfix/urgent-error`)
- **release/**: 배포 준비 브랜치 (ex: `release/v1.0.0`)

### 브랜치 생성 예시
```bash
git checkout -b feature/monitoring-api
git checkout -b fix/login-bug
```

---

## 2. 커밋 메시지 규칙
- `[YYYYMMDD] <type>: <내용>`
- type 예시: feat, fix, docs, refactor, test, chore
- 예시:
  - `[20240523] feat: 모니터링 API 엔드포인트 추가`
  - `[20240523] fix: 로그인 버그 수정`
  - `[20240523] docs: 개발 가이드 문서 추가`

---

## 3. Pull Request(PR) 규칙
- PR 제목: `[YYYYMMDD] <type>: <주요 변경점>`
- PR 설명: 변경 내용, 테스트 방법, 관련 이슈 등 상세히 작성
- 리뷰어 지정 및 코드리뷰 필수
- CI 통과 후 머지

---

## 4. 코드 스타일
- **Python**: PEP8 권장, Black 포매터 사용
- **PHP**: PSR-12 권장
- 함수/클래스/변수명은 명확하게 작성
- 주석은 한글/영문 혼용 가능, 반드시 필요한 곳에만 작성

### Python 포매팅 예시
```bash
black .
```

---

## 5. 환경 변수 및 보안
- `.env` 파일은 절대 커밋 금지 (예시 파일은 `.env.example`로 제공)
- 비밀번호, API 키 등 민감 정보는 환경 변수로만 관리

---

## 6. 테스트
- 모든 PR은 테스트 코드 포함 권장
- `pytest`로 테스트 실행
- 커버리지 80% 이상 유지 권장

---

## 7. 문서화
- 모든 주요 기능/구조/설정은 `docs/`에 마크다운으로 문서화
- API 명세, DB 스키마, 배포 방법 등도 문서화

---

## 8. 협업 및 커뮤니케이션
- 이슈는 GitHub Issue로 관리
- 작업 시작 전 반드시 이슈 생성 및 할당
- 작업 완료 후 PR 생성, 리뷰 요청
- 리뷰 승인 후 머지
- 불필요한 파일/폴더는 `.gitignore`에 추가
- 궁금한 점은 슬랙/이슈/PR 코멘트로 적극 소통

---

## 9. 기타
- 커밋/PR/이슈/문서 등 모든 기록은 최대한 상세하게 남길 것
- 협업 중 궁금한 점은 언제든 질문 