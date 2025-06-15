// 인증 관련 함수들
const auth = {
    // 로그인 함수
    async login(email, password) {
        try {
            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });
            
            if (!response.ok) {
                throw new Error('로그인에 실패했습니다.');
            }
            
            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            window.location.href = '/frontend/index.html';
        } catch (error) {
            console.error('로그인 오류:', error);
            alert(error.message);
        }
    },
    
    // 회원가입 함수
    async register(email, password, name) {
        try {
            const response = await fetch('/api/v1/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password, name }),
            });
            
            if (!response.ok) {
                throw new Error('회원가입에 실패했습니다.');
            }
            
            alert('회원가입이 완료되었습니다. 로그인해주세요.');
            window.location.href = '/frontend/login.html';
        } catch (error) {
            console.error('회원가입 오류:', error);
            alert(error.message);
        }
    },
    
    // 로그아웃 함수
    logout() {
        localStorage.removeItem('token');
        window.location.href = '/frontend/login.html';
    },
    
    // 토큰 확인 함수
    checkAuth() {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/frontend/login.html';
            return false;
        }
        return true;
    }
}; 