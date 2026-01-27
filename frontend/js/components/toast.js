/**
 * PyMonitor - 토스트 알림 모듈
 */

const toast = {
    container: null,

    /**
     * 초기화 (컨테이너 설정)
     */
    init(containerId = 'toast-container') {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.warn('Toast container not found:', containerId);
        }
    },

    /**
     * 토스트 알림 표시
     * @param {string} message - 메시지
     * @param {string} type - 타입 (info, success, error, warning)
     * @param {number} duration - 표시 시간 (ms)
     */
    show(message, type = 'info', duration = 3000) {
        if (!this.container) {
            this.init();
        }

        if (!this.container) {
            console.error('Toast container not available');
            return;
        }

        const toastEl = document.createElement('div');
        toastEl.className = `toast toast-${type}`;
        toastEl.textContent = message;

        this.container.appendChild(toastEl);

        // 애니메이션을 위한 딜레이
        setTimeout(() => toastEl.classList.add('show'), 10);

        // 지정 시간 후 제거
        setTimeout(() => {
            toastEl.classList.remove('show');
            setTimeout(() => toastEl.remove(), 300);
        }, duration);
    },

    /**
     * 성공 토스트
     */
    success(message, duration) {
        this.show(message, 'success', duration);
    },

    /**
     * 에러 토스트
     */
    error(message, duration) {
        this.show(message, 'error', duration);
    },

    /**
     * 경고 토스트
     */
    warning(message, duration) {
        this.show(message, 'warning', duration);
    },

    /**
     * 정보 토스트
     */
    info(message, duration) {
        this.show(message, 'info', duration);
    }
};

// 전역으로 노출
window.toast = toast;

// 기존 showToast 함수 호환성 유지
window.showToast = function(message, type = 'info') {
    toast.show(message, type);
};
