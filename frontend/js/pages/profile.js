/**
 * PyMonitor - 프로필 페이지 모듈
 */

const profilePage = {
    user: null,

    /**
     * 초기화
     */
    init() {
        if (!auth.checkAuth()) return;

        this.loadUserData();
        this.setupEventListeners();
    },

    /**
     * 사용자 데이터 로드
     */
    async loadUserData() {
        try {
            const response = await fetch('/api/v1/auth/me', {
                headers: auth.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('사용자 정보를 불러올 수 없습니다');
            }

            this.user = await response.json();
            this.populateForm();
        } catch (error) {
            console.error('사용자 데이터 로드 오류:', error);
            showToast('사용자 정보를 불러오는데 실패했습니다.', 'error');
        }
    },

    /**
     * 폼에 데이터 채우기
     */
    populateForm() {
        if (!this.user) return;

        // 헤더 유저 이름
        const userNameEl = document.getElementById('user-name');
        if (userNameEl) {
            userNameEl.textContent = this.user.full_name || this.user.email;
        }

        // 기본 정보
        document.getElementById('profile-email').value = this.user.email || '';
        document.getElementById('profile-name').value = this.user.full_name || '';
        document.getElementById('profile-phone').value = this.user.phone || '';

        // 환경 설정
        document.getElementById('theme-setting').value = this.user.theme || 'light';
        document.getElementById('language-setting').value = this.user.language || 'ko';
        document.getElementById('timezone-setting').value = this.user.timezone || 'Asia/Seoul';
        document.getElementById('email-notifications').checked = this.user.email_notifications !== false;

        // 계정 정보
        document.getElementById('profile-created-at').textContent = utils.formatDateTime(this.user.created_at);
        document.getElementById('profile-last-login').textContent = utils.formatDateTime(this.user.last_login_at);

        const statusEl = document.getElementById('profile-status');
        if (this.user.is_active) {
            statusEl.innerHTML = '<span class="badge badge-success">활성</span>';
        } else {
            statusEl.innerHTML = '<span class="badge badge-error">비활성</span>';
        }

        // 역할 표시
        const roleEl = document.getElementById('profile-role');
        if (roleEl) {
            const roleMap = {
                admin: '관리자',
                manager: '매니저',
                user: '사용자',
                viewer: '뷰어'
            };
            roleEl.textContent = roleMap[this.user.role] || this.user.role;
        }
    },

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        // 프로필 정보 저장
        const profileForm = document.getElementById('profile-form');
        if (profileForm) {
            profileForm.addEventListener('submit', (e) => this.handleProfileSubmit(e));
        }

        // 비밀번호 변경
        const passwordForm = document.getElementById('password-form');
        if (passwordForm) {
            passwordForm.addEventListener('submit', (e) => this.handlePasswordSubmit(e));
        }

        // 환경 설정 저장
        const settingsForm = document.getElementById('settings-form');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => this.handleSettingsSubmit(e));
        }
    },

    /**
     * 프로필 정보 저장
     */
    async handleProfileSubmit(e) {
        e.preventDefault();

        const submitBtn = e.target.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = '저장 중...';

        try {
            const response = await fetch('/api/v1/auth/me', {
                method: 'PUT',
                headers: auth.getAuthHeaders(),
                body: JSON.stringify({
                    full_name: document.getElementById('profile-name').value.trim() || null,
                    phone: document.getElementById('profile-phone').value.trim() || null,
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '프로필 저장에 실패했습니다');
            }

            const updatedUser = await response.json();
            localStorage.setItem('user', JSON.stringify(updatedUser));
            this.user = updatedUser;
            this.populateForm();
            showToast('프로필이 저장되었습니다.', 'success');
        } catch (error) {
            console.error('프로필 저장 오류:', error);
            showToast(error.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = '정보 저장';
        }
    },

    /**
     * 비밀번호 변경
     */
    async handlePasswordSubmit(e) {
        e.preventDefault();

        const errorEl = document.getElementById('password-error');
        errorEl.style.display = 'none';

        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        // 클라이언트 검증
        if (newPassword !== confirmPassword) {
            errorEl.textContent = '새 비밀번호가 일치하지 않습니다.';
            errorEl.style.display = 'block';
            return;
        }

        if (newPassword.length < 8) {
            errorEl.textContent = '비밀번호는 8자 이상이어야 합니다.';
            errorEl.style.display = 'block';
            return;
        }

        const submitBtn = e.target.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = '변경 중...';

        try {
            const response = await fetch('/api/v1/auth/me/password', {
                method: 'PUT',
                headers: auth.getAuthHeaders(),
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword,
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '비밀번호 변경에 실패했습니다');
            }

            // 폼 초기화
            document.getElementById('current-password').value = '';
            document.getElementById('new-password').value = '';
            document.getElementById('confirm-password').value = '';
            showToast('비밀번호가 변경되었습니다.', 'success');
        } catch (error) {
            console.error('비밀번호 변경 오류:', error);
            errorEl.textContent = error.message;
            errorEl.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = '비밀번호 변경';
        }
    },

    /**
     * 환경 설정 저장
     */
    async handleSettingsSubmit(e) {
        e.preventDefault();

        const submitBtn = e.target.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = '저장 중...';

        const theme = document.getElementById('theme-setting').value;
        const language = document.getElementById('language-setting').value;
        const timezone = document.getElementById('timezone-setting').value;
        const emailNotifications = document.getElementById('email-notifications').checked;

        try {
            const response = await fetch('/api/v1/auth/me/settings', {
                method: 'PUT',
                headers: auth.getAuthHeaders(),
                body: JSON.stringify({
                    theme: theme,
                    language: language,
                    timezone: timezone,
                    email_notifications: emailNotifications,
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '설정 저장에 실패했습니다');
            }

            // 테마 즉시 적용
            if (window.themeManager) {
                window.themeManager.setTheme(theme);
            }

            // 로컬 사용자 데이터 업데이트
            this.user.theme = theme;
            this.user.language = language;
            this.user.timezone = timezone;
            this.user.email_notifications = emailNotifications;
            localStorage.setItem('user', JSON.stringify(this.user));

            showToast('설정이 저장되었습니다.', 'success');
        } catch (error) {
            console.error('설정 저장 오류:', error);
            showToast(error.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = '설정 저장';
        }
    }
};

// 전역으로 노출
window.profilePage = profilePage;

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => profilePage.init());
