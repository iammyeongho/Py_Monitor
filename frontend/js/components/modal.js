/**
 * PyMonitor - 모달 관리 모듈
 */

const modal = {
    /**
     * 모달 열기
     * @param {string} modalId - 모달 요소 ID
     */
    open(modalId) {
        const modalEl = document.getElementById(modalId);
        if (modalEl) {
            modalEl.classList.add('active');
        }
    },

    /**
     * 모달 닫기
     * @param {string} modalId - 모달 요소 ID
     */
    close(modalId) {
        const modalEl = document.getElementById(modalId);
        if (modalEl) {
            modalEl.classList.remove('active');
        }
    },

    /**
     * 모달 토글
     * @param {string} modalId - 모달 요소 ID
     */
    toggle(modalId) {
        const modalEl = document.getElementById(modalId);
        if (modalEl) {
            modalEl.classList.toggle('active');
        }
    },

    /**
     * 모달 외부 클릭 시 닫기 설정
     * @param {string} modalId - 모달 요소 ID
     */
    setupOutsideClick(modalId) {
        const modalEl = document.getElementById(modalId);
        if (modalEl) {
            modalEl.addEventListener('click', (e) => {
                if (e.target === modalEl) {
                    this.close(modalId);
                }
            });
        }
    },

    /**
     * 모든 모달에 외부 클릭 닫기 설정
     */
    setupAllOutsideClick() {
        document.querySelectorAll('.modal').forEach(modalEl => {
            modalEl.addEventListener('click', (e) => {
                if (e.target === modalEl) {
                    modalEl.classList.remove('active');
                }
            });
        });
    },

    /**
     * 탭 전환 설정
     * @param {string} tabSelector - 탭 버튼 선택자
     * @param {string} contentSelector - 탭 컨텐츠 선택자
     * @param {Function} onTabChange - 탭 변경 콜백
     */
    setupTabs(tabSelector, contentSelector, onTabChange) {
        document.querySelectorAll(tabSelector).forEach(tab => {
            tab.addEventListener('click', () => {
                const tabId = tab.dataset.tab;

                // 탭 버튼 활성화
                document.querySelectorAll(tabSelector).forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                // 탭 컨텐츠 활성화
                document.querySelectorAll(contentSelector).forEach(c => c.classList.remove('active'));
                const contentEl = document.getElementById(`tab-${tabId}`);
                if (contentEl) {
                    contentEl.classList.add('active');
                }

                // 콜백 실행
                if (onTabChange) {
                    onTabChange(tabId);
                }
            });
        });
    }
};

// 전역으로 노출
window.modal = modal;
