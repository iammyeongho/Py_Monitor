/**
 * PyMonitor - 공통 헤더 컴포넌트
 * 모든 페이지에서 동일한 헤더를 렌더링합니다.
 */

const Header = {
    /**
     * 네비게이션 메뉴 정의
     */
    NAV_ITEMS: [
        { href: 'index.html', label: '대시보드' },
        { href: 'project.html', label: '프로젝트 등록' },
        { href: 'tools.html', label: '도구' },
        { href: 'status.html', label: '상태 페이지' },
    ],

    /**
     * 현재 페이지 파일명 추출
     */
    getCurrentPage() {
        const path = window.location.pathname;
        const filename = path.split('/').pop();
        return filename || 'index.html';
    },

    /**
     * 헤더 HTML 생성
     */
    render() {
        const currentPage = this.getCurrentPage();

        const navLinks = this.NAV_ITEMS.map(item => {
            const isActive = item.href === currentPage ? ' active' : '';
            return `<a href="${item.href}" class="nav-link${isActive}">${item.label}</a>`;
        }).join('\n        ');

        const isProfilePage = currentPage === 'profile.html';
        const userNameClass = isProfilePage ? 'user-name active' : 'user-name';

        return `
    <div class="header-inner">
      <a href="index.html" class="logo">PyMonitor</a>
      <nav class="nav">
        ${navLinks}
      </nav>
      <div class="user-actions">
        <a href="profile.html" class="${userNameClass}" id="user-name"></a>
        <button class="btn btn-secondary btn-sm" id="logout-btn">로그아웃</button>
      </div>
    </div>`;
    },

    /**
     * 헤더 초기화 - DOM에 삽입 및 이벤트 바인딩
     */
    init() {
        const headerEl = document.getElementById('app-header');
        if (!headerEl) return;

        headerEl.innerHTML = this.render();

        // 유저 이름 표시
        this.displayUserName();

        // 로그아웃 버튼
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => auth.logout());
        }
    },

    /**
     * 유저 이름 표시
     */
    displayUserName() {
        const user = auth.getUser();
        const userNameEl = document.getElementById('user-name');
        if (user && userNameEl) {
            userNameEl.textContent = user.full_name || user.email;
        }
    }
};

// 전역으로 노출
window.Header = Header;

// DOM 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => Header.init());
