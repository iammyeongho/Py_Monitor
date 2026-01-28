/**
 * 테마 관리 컴포넌트
 * 우측 하단 플로팅 버튼으로 테마 전환
 */

const ThemeManager = {
  STORAGE_KEY: 'py_monitor_theme',
  THEMES: {
    LIGHT: 'light',
    DARK: 'dark'
  },

  // SVG 아이콘
  ICONS: {
    sun: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="5"></circle>
      <line x1="12" y1="1" x2="12" y2="3"></line>
      <line x1="12" y1="21" x2="12" y2="23"></line>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
      <line x1="1" y1="12" x2="3" y2="12"></line>
      <line x1="21" y1="12" x2="23" y2="12"></line>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
    </svg>`,
    moon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
    </svg>`
  },

  /**
   * 초기화
   */
  init() {
    this.createFloatingButton();
    this.applyTheme(this.getStoredTheme());
    this.setupSystemThemeListener();
  },

  /**
   * 플로팅 버튼 생성
   */
  createFloatingButton() {
    // 기존 버튼 제거 (헤더에 있던 것)
    const oldButton = document.getElementById('theme-toggle');
    if (oldButton) {
      oldButton.remove();
    }

    // 플로팅 버튼 생성
    const button = document.createElement('button');
    button.id = 'theme-floating-btn';
    button.className = 'theme-floating-btn';
    button.setAttribute('title', '테마 변경');
    button.innerHTML = `<span class="theme-btn-icon" id="theme-icon">${this.ICONS.moon}</span>`;

    document.body.appendChild(button);

    // 클릭 이벤트
    button.addEventListener('click', () => this.toggleTheme());
  },

  /**
   * 저장된 테마 가져오기
   */
  getStoredTheme() {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    if (stored) return stored;

    // 시스템 설정 확인
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? this.THEMES.DARK
      : this.THEMES.LIGHT;
  },

  /**
   * 테마 저장
   */
  setStoredTheme(theme) {
    localStorage.setItem(this.STORAGE_KEY, theme);
  },

  /**
   * 테마 적용
   */
  applyTheme(theme) {
    const root = document.documentElement;
    root.setAttribute('data-theme', theme);
    this.updateIcon(theme);

    // body 클래스도 추가 (일부 스타일 호환성)
    document.body.classList.remove('theme-light', 'theme-dark');
    document.body.classList.add(`theme-${theme}`);
  },

  /**
   * 아이콘 업데이트
   */
  updateIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (icon) {
      // 다크모드일 때 해(sun) 아이콘, 라이트모드일 때 달(moon) 아이콘
      icon.innerHTML = theme === this.THEMES.DARK ? this.ICONS.sun : this.ICONS.moon;
    }
  },

  /**
   * 테마 토글
   */
  toggleTheme() {
    const currentTheme = this.getStoredTheme();
    const newTheme = currentTheme === this.THEMES.LIGHT
      ? this.THEMES.DARK
      : this.THEMES.LIGHT;

    this.setStoredTheme(newTheme);
    this.applyTheme(newTheme);
    this.saveToServer(newTheme);

    // 토스트 메시지
    if (typeof Toast !== 'undefined') {
      const themeNames = {
        light: '라이트 모드',
        dark: '다크 모드'
      };
      Toast.info(`테마: ${themeNames[newTheme]}`);
    }
  },

  /**
   * 시스템 테마 변경 감지
   */
  setupSystemThemeListener() {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', (e) => {
      // 저장된 테마가 없을 때만 시스템 설정 따름
      if (!localStorage.getItem(this.STORAGE_KEY)) {
        const newTheme = e.matches ? this.THEMES.DARK : this.THEMES.LIGHT;
        this.applyTheme(newTheme);
      }
    });
  },

  /**
   * 서버에 테마 저장
   */
  async saveToServer(theme) {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      await fetch('/api/v1/auth/me/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ theme })
      });
    } catch (error) {
      console.log('Theme save failed:', error);
    }
  }
};

// DOM 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
  ThemeManager.init();
});
