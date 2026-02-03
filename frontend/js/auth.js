// 인증 관련 함수들
const auth = {
    // 401 에러 처리 중 플래그 (중복 로그아웃 방지)
    _isHandling401: false,

    // 401 에러 핸들러
    handle401() {
        if (this._isHandling401) return;
        this._isHandling401 = true;

        // 현재 페이지가 로그인 페이지가 아닐 때만 처리
        if (!window.location.pathname.includes('login.html')) {
            console.warn('세션이 만료되었습니다. 로그인 페이지로 이동합니다.');
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/frontend/html/login.html?expired=1';
        }
    },

    // 인증된 API 요청 (401 자동 처리)
    async apiRequest(url, options = {}) {
        const token = this.getToken();
        if (!token) {
            this.handle401();
            throw new Error('No token');
        }

        const headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers,
        };

        try {
            const response = await fetch(url, { ...options, headers });

            if (response.status === 401) {
                this.handle401();
                throw new Error('Unauthorized');
            }

            return response;
        } catch (error) {
            if (error.message === 'Unauthorized') {
                throw error;
            }
            throw error;
        }
    },

    // 로그인 함수
    async login(email, password) {
        try {
            // OAuth2 스펙에 따라 form data로 전송
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '로그인에 실패했습니다.');
            }

            const data = await response.json();
            localStorage.setItem('token', data.access_token);

            // 사용자 정보 가져오기
            await this.fetchAndStoreUser();

            window.location.href = '/frontend/html/index.html';
        } catch (error) {
            console.error('로그인 오류:', error);
            throw error;
        }
    },

    // 사용자 정보 가져오기
    async fetchAndStoreUser() {
        try {
            const response = await fetch('/api/v1/auth/me', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });

            if (response.ok) {
                const user = await response.json();
                localStorage.setItem('user', JSON.stringify(user));
            }
        } catch (error) {
            console.error('사용자 정보 조회 오류:', error);
        }
    },

    // 저장된 사용자 정보 가져오기
    getUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    },

    // 회원가입 함수
    async register(email, password, fullName) {
        try {
            const response = await fetch('/api/v1/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    full_name: fullName
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '회원가입에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('회원가입 오류:', error);
            throw error;
        }
    },

    // 로그아웃 함수
    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/frontend/html/login.html';
    },

    // 토큰 확인 함수
    checkAuth() {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/frontend/html/login.html';
            return false;
        }

        // 토큰 유효성 비동기 검증 (백그라운드)
        this.validateToken().catch(() => {
            this.logout();
        });

        return true;
    },

    // 토큰 유효성 검증
    async validateToken() {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('No token');
        }

        const response = await fetch('/api/v1/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error('Invalid token');
        }

        return await response.json();
    },

    // 토큰 가져오기
    getToken() {
        return localStorage.getItem('token');
    },

    // 인증 헤더 가져오기
    getAuthHeaders() {
        const token = this.getToken();
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        };
    }
};
