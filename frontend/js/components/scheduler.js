/**
 * PyMonitor - 스케줄러 컨트롤 모듈
 */

const scheduler = {
    // UI 요소 참조
    elements: {
        indicator: null,
        label: null,
        count: null,
        startBtn: null,
        stopBtn: null,
        refreshBtn: null
    },

    /**
     * 초기화
     */
    init() {
        this.elements = {
            indicator: document.getElementById('scheduler-indicator'),
            label: document.getElementById('scheduler-label'),
            count: document.getElementById('scheduler-count'),
            startBtn: document.getElementById('scheduler-start-btn'),
            stopBtn: document.getElementById('scheduler-stop-btn'),
            refreshBtn: document.getElementById('scheduler-refresh-btn')
        };

        this.setupEventListeners();
        this.loadStatus();
    },

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        if (this.elements.startBtn) {
            this.elements.startBtn.addEventListener('click', () => this.start());
        }
        if (this.elements.stopBtn) {
            this.elements.stopBtn.addEventListener('click', () => this.stop());
        }
        if (this.elements.refreshBtn) {
            this.elements.refreshBtn.addEventListener('click', () => this.loadStatus());
        }
    },

    /**
     * 스케줄러 상태 로드
     */
    async loadStatus() {
        try {
            const response = await fetch('/api/v1/monitoring/scheduler/status', {
                headers: auth.getAuthHeaders()
            });

            if (response.ok) {
                const status = await response.json();
                this.updateUI(status);
            } else {
                this.updateUI({ is_running: false, project_count: 0 });
            }
        } catch (error) {
            console.error('스케줄러 상태 로드 오류:', error);
            this.updateUI({ is_running: false, project_count: 0, error: true });
        }
    },

    /**
     * UI 업데이트
     */
    updateUI(status) {
        const { indicator, label, count, startBtn, stopBtn } = this.elements;

        if (!indicator || !label) return;

        if (status.error) {
            indicator.className = 'scheduler-indicator stopped';
            label.textContent = '상태 확인 실패';
            if (count) count.textContent = '';
            if (startBtn) startBtn.style.display = 'inline-block';
            if (stopBtn) stopBtn.style.display = 'none';
            return;
        }

        if (status.is_running) {
            indicator.className = 'scheduler-indicator running';
            label.textContent = '자동 모니터링 실행 중';
            if (count) count.textContent = `(${status.project_count}개 프로젝트)`;
            if (startBtn) startBtn.style.display = 'none';
            if (stopBtn) stopBtn.style.display = 'inline-block';
        } else {
            indicator.className = 'scheduler-indicator stopped';
            label.textContent = '자동 모니터링 중지됨';
            if (count) count.textContent = '';
            if (startBtn) startBtn.style.display = 'inline-block';
            if (stopBtn) stopBtn.style.display = 'none';
        }
    },

    /**
     * 스케줄러 시작
     */
    async start() {
        const { startBtn } = this.elements;
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.textContent = '시작 중...';
        }

        try {
            const response = await fetch('/api/v1/monitoring/scheduler/start', {
                method: 'POST',
                headers: auth.getAuthHeaders()
            });

            if (response.ok) {
                const result = await response.json();
                this.updateUI(result.status);
                showToast('스케줄러가 시작되었습니다.', 'success');
            } else {
                const error = await response.json();
                showToast(error.detail || '스케줄러 시작에 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('스케줄러 시작 오류:', error);
            showToast('스케줄러 시작 중 오류가 발생했습니다.', 'error');
        } finally {
            if (startBtn) {
                startBtn.disabled = false;
                startBtn.textContent = '스케줄러 시작';
            }
        }
    },

    /**
     * 스케줄러 중지
     */
    async stop() {
        if (!confirm('스케줄러를 중지하시겠습니까? 자동 모니터링이 중단됩니다.')) return;

        const { stopBtn } = this.elements;
        if (stopBtn) {
            stopBtn.disabled = true;
            stopBtn.textContent = '중지 중...';
        }

        try {
            const response = await fetch('/api/v1/monitoring/scheduler/stop', {
                method: 'POST',
                headers: auth.getAuthHeaders()
            });

            if (response.ok) {
                const result = await response.json();
                this.updateUI(result.status);
                showToast('스케줄러가 중지되었습니다.', 'success');
            } else {
                const error = await response.json();
                showToast(error.detail || '스케줄러 중지에 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('스케줄러 중지 오류:', error);
            showToast('스케줄러 중지 중 오류가 발생했습니다.', 'error');
        } finally {
            if (stopBtn) {
                stopBtn.disabled = false;
                stopBtn.textContent = '스케줄러 중지';
            }
        }
    }
};

// 전역으로 노출
window.scheduler = scheduler;
