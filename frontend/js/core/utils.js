/**
 * PyMonitor - 유틸리티 함수 모듈
 */

const utils = {
    /**
     * HTML 이스케이프
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * 상대적 시간 포맷 (방금 전, 5분 전 등)
     */
    formatTime(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return '방금 전';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}분 전`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}시간 전`;
        return `${Math.floor(diff / 86400000)}일 전`;
    },

    /**
     * 날짜+시간 포맷
     */
    formatDateTime(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleString('ko-KR');
    },

    /**
     * 날짜만 포맷
     */
    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR');
    },

    /**
     * 응답시간 포맷 (초 -> ms)
     */
    formatResponseTime(seconds) {
        if (seconds === null || seconds === undefined) return '-';
        return `${Math.round(seconds * 1000)}ms`;
    },

    /**
     * 바이트 크기 포맷
     */
    formatBytes(bytes) {
        if (bytes === null || bytes === undefined) return '-';
        if (bytes < 1024) return `${bytes}B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
        return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
    }
};

// 전역으로 노출
window.utils = utils;
