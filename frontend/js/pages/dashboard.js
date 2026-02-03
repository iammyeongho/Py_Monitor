/**
 * PyMonitor - 대시보드 페이지 모듈
 */

const dashboard = {
    // 상태
    currentProjectId: null,
    projects: [],
    refreshInterval: null,
    refreshIntervalMs: 60000, // 기본 1분 자동 새로고침

    /**
     * 초기화
     */
    init() {
        if (!auth.checkAuth()) return;

        this.loadProjects();
        scheduler.init();
        chartManager.init();
        this.setupEventListeners();
        this.startAutoRefresh();
    },

    /**
     * 자동 새로고침 시작
     */
    startAutoRefresh() {
        // 기존 인터벌 정리
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        // 모니터링 상태만 주기적으로 새로고침 (전체 페이지 리로드 없이)
        this.refreshInterval = setInterval(() => {
            if (!document.hidden) {
                this.loadMonitoringStatus();
            }
        }, this.refreshIntervalMs);

        // 페이지 visibility 변경 시 처리
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // 탭이 다시 활성화되면 즉시 새로고침
                this.loadMonitoringStatus();
            }
        });
    },

    /**
     * 자동 새로고침 중지
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    },

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        // 설정 모달
        const closeSettingBtn = document.getElementById('close-setting-modal');
        const cancelSettingBtn = document.getElementById('cancel-setting');
        if (closeSettingBtn) closeSettingBtn.addEventListener('click', () => this.closeSettingModal());
        if (cancelSettingBtn) cancelSettingBtn.addEventListener('click', () => this.closeSettingModal());

        // 상세 모달
        const closeDetailBtn = document.getElementById('close-detail-modal');
        if (closeDetailBtn) closeDetailBtn.addEventListener('click', () => this.closeDetailModal());

        // 폼 제출
        const settingForm = document.getElementById('setting-form');
        const detailSettingForm = document.getElementById('detail-setting-form');
        if (settingForm) settingForm.addEventListener('submit', (e) => this.handleSettingSubmit(e));
        if (detailSettingForm) detailSettingForm.addEventListener('submit', (e) => this.handleDetailSettingSubmit(e));

        // 프로젝트 삭제
        const deleteBtn = document.getElementById('delete-project-btn');
        if (deleteBtn) deleteBtn.addEventListener('click', () => this.handleDeleteProject());

        // 심층 체크
        const deepCheckBtn = document.getElementById('run-deep-check-btn');
        if (deepCheckBtn) deepCheckBtn.addEventListener('click', () => this.runDeepCheck());

        // 모달 외부 클릭
        modal.setupAllOutsideClick();

        // 상세 모달 탭
        modal.setupTabs('.modal-tab', '.modal-tab-content', (tabId) => {
            if (tabId === 'detail-history' && this.currentProjectId) {
                this.loadMonitoringHistory(this.currentProjectId);
            }
        });
    },

    /**
     * 프로젝트 목록 로드
     */
    async loadProjects() {
        const grid = document.getElementById('projects-grid');
        const loading = document.getElementById('loading');
        const emptyState = document.getElementById('empty-state');

        try {
            this.projects = await project.getProjects();

            if (loading) loading.style.display = 'none';

            if (this.projects.length === 0) {
                if (grid) grid.style.display = 'none';
                if (emptyState) emptyState.style.display = 'flex';
                this.updateStats(0, 0, 0, '-');
                return;
            }

            if (emptyState) emptyState.style.display = 'none';
            if (grid) grid.style.display = 'grid';

            this.renderProjects();
            await this.loadMonitoringStatus();
            this.updateStatsFromProjects();
            this.captureAllScreenshots();

        } catch (error) {
            console.error('프로젝트 로드 오류:', error);
            if (loading) loading.innerHTML = '<p class="text-error">프로젝트를 불러오는데 실패했습니다.</p>';
            showToast('프로젝트 목록을 불러오는데 실패했습니다.', 'error');
        }
    },

    /**
     * 모니터링 상태 로드
     */
    async loadMonitoringStatus() {
        try {
            const statuses = await monitoring.getAllProjectsStatus();

            statuses.forEach(status => {
                const proj = this.projects.find(p => p.id === status.project_id);
                if (proj) {
                    proj.monitoringStatus = status;
                    proj.is_available = status.status?.is_available ?? null;
                    proj.response_time = status.status?.response_time;
                    proj.status_code = status.status?.status_code;
                    proj.error_message = status.status?.error_message;
                    proj.ssl_info = status.ssl;
                    proj.last_checked_at = status.checked_at;
                }
            });

            this.renderProjects();
        } catch (error) {
            console.error('모니터링 상태 로드 오류:', error);
        }
    },

    /**
     * 프로젝트 렌더링
     */
    renderProjects() {
        const grid = document.getElementById('projects-grid');
        if (!grid) return;
        grid.innerHTML = this.projects.map(p => this.createProjectCard(p)).join('');
    },

    /**
     * 프로젝트 카드 생성
     */
    createProjectCard(proj) {
        let statusClass, statusText;
        if (proj.is_available === null || proj.is_available === undefined) {
            statusClass = 'status-pending';
            statusText = '대기중';
        } else if (proj.is_available === true) {
            statusClass = 'status-online';
            statusText = '정상';
        } else {
            statusClass = 'status-offline';
            statusText = '오류';
        }

        const responseTime = proj.response_time ? `${Math.round(proj.response_time * 1000)}ms` : '-';
        const statusCode = proj.status_code ? `HTTP ${proj.status_code}` : '';

        let sslBadge = '';
        if (proj.ssl_info) {
            if (proj.ssl_info.is_valid) {
                const daysRemaining = proj.ssl_info.days_remaining;
                if (daysRemaining !== null && daysRemaining <= 30) {
                    sslBadge = `<span class="ssl-badge ssl-warning" title="SSL 만료 ${daysRemaining}일 전">SSL ${daysRemaining}일</span>`;
                } else {
                    sslBadge = '<span class="ssl-badge ssl-valid" title="SSL 유효">SSL</span>';
                }
            } else {
                sslBadge = '<span class="ssl-badge ssl-invalid" title="SSL 오류">SSL 오류</span>';
            }
        }

        const thumbnailUrl = this.getThumbnailUrl(proj.url, proj.snapshot_path);

        return `
            <div class="project-card" data-id="${proj.id}">
                <div class="project-thumbnail" onclick="dashboard.openDetailModal(${proj.id})">
                    <img src="${thumbnailUrl}" alt="${utils.escapeHtml(proj.title)}" loading="lazy" onerror="this.src='/frontend/img/placeholder.svg'; this.onerror=null;">
                    <div class="thumbnail-overlay">
                        <div class="status-group">
                            <span class="project-status ${statusClass}">${statusText}</span>
                            ${sslBadge}
                        </div>
                    </div>
                </div>
                <div class="project-card-body" onclick="dashboard.openDetailModal(${proj.id})">
                    <h3 class="project-title">${utils.escapeHtml(proj.title)}</h3>
                    <p class="project-url">${utils.escapeHtml(proj.url)}</p>
                    ${proj.error_message ? `<p class="project-error">${utils.escapeHtml(proj.error_message)}</p>` : ''}
                </div>
                <div class="project-card-footer">
                    <div class="project-stat">
                        <span class="project-stat-label">응답시간</span>
                        <span class="project-stat-value">${responseTime}</span>
                    </div>
                    <div class="project-stat">
                        <span class="project-stat-label">상태코드</span>
                        <span class="project-stat-value">${statusCode || '-'}</span>
                    </div>
                    <div class="project-stat">
                        <span class="project-stat-label">마지막 체크</span>
                        <span class="project-stat-value">${utils.formatTime(proj.last_checked_at)}</span>
                    </div>
                </div>
                <button class="project-menu-btn" onclick="event.stopPropagation(); dashboard.openSettingModal(${proj.id})">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="1"></circle>
                        <circle cx="12" cy="5" r="1"></circle>
                        <circle cx="12" cy="19" r="1"></circle>
                    </svg>
                </button>
            </div>
        `;
    },

    /**
     * 통계 업데이트
     */
    updateStats(total, online, offline, avgResponse) {
        const statTotal = document.getElementById('stat-total');
        const statOnline = document.getElementById('stat-online');
        const statOffline = document.getElementById('stat-offline');
        const statResponse = document.getElementById('stat-response');

        if (statTotal) statTotal.textContent = total;
        if (statOnline) statOnline.textContent = online;
        if (statOffline) statOffline.textContent = offline;
        if (statResponse) statResponse.textContent = avgResponse;
    },

    /**
     * 프로젝트 데이터로 통계 업데이트
     */
    updateStatsFromProjects() {
        const total = this.projects.length;
        const online = this.projects.filter(p => p.is_available === true).length;
        const offline = this.projects.filter(p => p.is_available === false).length;

        const responseTimes = this.projects
            .filter(p => p.response_time !== null && p.response_time !== undefined)
            .map(p => p.response_time * 1000);

        const avgResponse = responseTimes.length > 0
            ? Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length) + 'ms'
            : '-';

        this.updateStats(total, online, offline, avgResponse);
    },

    /**
     * 썸네일 URL 가져오기
     */
    getThumbnailUrl(url, cachedPath) {
        if (cachedPath) return cachedPath;
        return '/frontend/img/placeholder.svg';
    },

    /**
     * 스크린샷 캡처
     */
    async captureScreenshot(projectId) {
        try {
            const response = await fetch(`/api/v1/projects/${projectId}/screenshot?force=false`, {
                headers: auth.getAuthHeaders()
            });
            if (response.ok) {
                const data = await response.json();
                return data.screenshot_url;
            }
        } catch (error) {
            console.error('스크린샷 캡처 오류:', error);
        }
        return null;
    },

    /**
     * 모든 프로젝트 스크린샷 캡처
     */
    async captureAllScreenshots() {
        for (const proj of this.projects) {
            if (!proj.snapshot_path) {
                const screenshotUrl = await this.captureScreenshot(proj.id);
                if (screenshotUrl) {
                    proj.snapshot_path = screenshotUrl;
                    const card = document.querySelector(`.project-card[data-id="${proj.id}"]`);
                    if (card) {
                        const img = card.querySelector('.project-thumbnail img');
                        if (img) img.src = screenshotUrl;
                    }
                }
            }
        }
    },

    /**
     * 설정 모달 열기
     */
    openSettingModal(projectId) {
        this.currentProjectId = projectId;
        modal.open('setting-modal');
    },

    /**
     * 설정 모달 닫기
     */
    closeSettingModal() {
        modal.close('setting-modal');
        this.currentProjectId = null;
    },

    /**
     * 상세 모달 열기
     */
    async openDetailModal(projectId) {
        this.currentProjectId = projectId;

        try {
            const proj = this.projects.find(p => p.id === projectId);
            if (!proj) return;

            document.getElementById('detail-title').textContent = proj.title;
            document.getElementById('detail-url').textContent = proj.url;

            // 상태 표시
            let statusHtml;
            if (proj.is_available === null || proj.is_available === undefined) {
                statusHtml = '<span class="badge badge-pending">대기중</span>';
            } else if (proj.is_available === true) {
                statusHtml = '<span class="badge badge-success">정상</span>';
            } else {
                statusHtml = '<span class="badge badge-error">오류</span>';
            }
            if (proj.status_code) {
                statusHtml += ` <span class="badge badge-info">HTTP ${proj.status_code}</span>`;
            }
            document.getElementById('detail-status').innerHTML = statusHtml;

            document.getElementById('detail-response-time').textContent = utils.formatResponseTime(proj.response_time);
            document.getElementById('detail-last-check').textContent = utils.formatDateTime(proj.last_checked_at);

            // SSL 정보
            if (proj.ssl_info) {
                const ssl = proj.ssl_info;
                if (ssl.is_valid) {
                    document.getElementById('detail-ssl-status').innerHTML = '<span class="badge badge-success">유효</span>';
                    if (ssl.valid_until) {
                        document.getElementById('detail-ssl-expiry').textContent =
                            `${utils.formatDate(ssl.valid_until)} (${ssl.days_remaining}일 남음)`;
                    }
                } else {
                    document.getElementById('detail-ssl-status').innerHTML = '<span class="badge badge-error">오류</span>';
                    document.getElementById('detail-ssl-expiry').textContent = '-';
                }
            } else {
                document.getElementById('detail-ssl-status').textContent = '-';
                document.getElementById('detail-ssl-expiry').textContent = '-';
            }

            document.getElementById('detail-domain-expiry').textContent =
                proj.domain_expiry_date ? utils.formatDate(proj.domain_expiry_date) : '-';

            // 심층 모니터링 데이터
            this.loadDeepMonitoringData(projectId);

            // 모니터링 설정 로드
            await this.loadDetailSettings(projectId);

            modal.open('detail-modal');

        } catch (error) {
            console.error('상세 정보 로드 오류:', error);
            showToast('상세 정보를 불러오는데 실패했습니다.', 'error');
        }
    },

    /**
     * 상세 설정 로드
     */
    async loadDetailSettings(projectId) {
        // 프로젝트 공개 설정 로드 (프로젝트 데이터에서)
        const proj = this.projects.find(p => p.id === projectId);
        document.getElementById('detail-is-public').checked = proj?.is_public || false;

        try {
            const settings = await monitoring.getSettings(projectId);
            document.getElementById('detail-check-interval').value = settings.check_interval || 300;
            document.getElementById('detail-timeout').value = settings.timeout || 30;
            document.getElementById('detail-retry-count').value = settings.retry_count || 3;
            document.getElementById('detail-alert-threshold').value = settings.alert_threshold || 3;
            document.getElementById('detail-response-limit').value = settings.response_time_limit || 5;
            document.getElementById('detail-expiry-dday').value = settings.expiry_alert_days || 30;
            document.getElementById('detail-alert-enabled').checked = settings.is_alert_enabled !== false;
            document.getElementById('detail-alert-email').value = settings.alert_email || '';
            document.getElementById('detail-webhook-url').value = settings.webhook_url || '';
        } catch (error) {
            console.warn('모니터링 설정 로드 실패:', error);
            // 기본값 설정
            document.getElementById('detail-check-interval').value = 300;
            document.getElementById('detail-timeout').value = 30;
            document.getElementById('detail-retry-count').value = 3;
            document.getElementById('detail-alert-threshold').value = 3;
            document.getElementById('detail-response-limit').value = 5;
            document.getElementById('detail-expiry-dday').value = 30;
            document.getElementById('detail-alert-enabled').checked = true;
            document.getElementById('detail-alert-email').value = '';
            document.getElementById('detail-webhook-url').value = '';
        }
    },

    /**
     * 상세 모달 닫기
     */
    closeDetailModal() {
        modal.close('detail-modal');
        this.currentProjectId = null;
    },

    /**
     * 설정 폼 제출
     */
    async handleSettingSubmit(e) {
        e.preventDefault();

        const settings = {
            check_interval: parseInt(document.getElementById('check-interval').value),
            timeout: parseInt(document.getElementById('timeout').value),
            retry_count: parseInt(document.getElementById('retry-count').value),
            alert_threshold: parseInt(document.getElementById('alert-threshold').value)
        };

        try {
            await monitoring.updateSettings(this.currentProjectId, settings);
            showToast('설정이 저장되었습니다.', 'success');
            this.closeSettingModal();
            this.loadProjects();
        } catch (error) {
            console.error('설정 저장 오류:', error);
            showToast('설정 저장에 실패했습니다.', 'error');
        }
    },

    /**
     * 상세 설정 폼 제출
     */
    async handleDetailSettingSubmit(e) {
        e.preventDefault();

        const alertEmail = document.getElementById('detail-alert-email').value.trim();
        const webhookUrl = document.getElementById('detail-webhook-url').value.trim();
        const isPublic = document.getElementById('detail-is-public').checked;

        const settings = {
            check_interval: parseInt(document.getElementById('detail-check-interval').value),
            timeout: parseInt(document.getElementById('detail-timeout').value),
            retry_count: parseInt(document.getElementById('detail-retry-count').value),
            alert_threshold: parseInt(document.getElementById('detail-alert-threshold').value),
            response_time_limit: parseInt(document.getElementById('detail-response-limit').value),
            expiry_alert_days: parseInt(document.getElementById('detail-expiry-dday').value),
            is_alert_enabled: document.getElementById('detail-alert-enabled').checked,
            alert_email: alertEmail || null,
            webhook_url: webhookUrl || null
        };

        try {
            // 모니터링 설정 저장
            await monitoring.updateSettings(this.currentProjectId, settings);

            // 프로젝트 공개 설정 저장
            const proj = this.projects.find(p => p.id === this.currentProjectId);
            if (proj && proj.is_public !== isPublic) {
                await project.updateProject(this.currentProjectId, {
                    title: proj.title,
                    url: proj.url,
                    is_public: isPublic,
                });
            }

            showToast('설정이 저장되었습니다.', 'success');
            this.closeDetailModal();
            this.loadProjects();
        } catch (error) {
            console.error('설정 저장 오류:', error);
            showToast('설정 저장에 실패했습니다.', 'error');
        }
    },

    /**
     * 프로젝트 삭제
     */
    async handleDeleteProject() {
        if (!confirm('정말 이 프로젝트를 삭제하시겠습니까?')) return;

        try {
            await project.deleteProject(this.currentProjectId);
            showToast('프로젝트가 삭제되었습니다.', 'success');
            this.closeDetailModal();
            this.loadProjects();
        } catch (error) {
            console.error('프로젝트 삭제 오류:', error);
            showToast('프로젝트 삭제에 실패했습니다.', 'error');
        }
    },

    /**
     * 모니터링 히스토리 로드
     */
    async loadMonitoringHistory(projectId) {
        const historyList = document.getElementById('history-list');
        if (!historyList) return;

        historyList.innerHTML = `
            <div class="loading">
                <div class="loading-spinner"></div>
                <p>로딩 중...</p>
            </div>
        `;

        try {
            const logs = await monitoring.getLogs(projectId, 0, 50);

            if (logs.length === 0) {
                historyList.innerHTML = '<p class="empty-message">모니터링 기록이 없습니다.</p>';
                return;
            }

            historyList.innerHTML = logs.map(log => `
                <div class="history-item ${log.is_available ? 'history-success' : 'history-error'}">
                    <div class="history-status">
                        <span class="history-icon">${log.is_available ? '✓' : '✗'}</span>
                        <span class="history-time">${utils.formatDateTime(log.created_at)}</span>
                    </div>
                    <div class="history-details">
                        ${log.status_code ? `<span class="history-code">HTTP ${log.status_code}</span>` : ''}
                        ${log.response_time ? `<span class="history-response">${Math.round(log.response_time * 1000)}ms</span>` : ''}
                        ${log.error_message ? `<span class="history-error-msg">${utils.escapeHtml(log.error_message)}</span>` : ''}
                    </div>
                </div>
            `).join('');

        } catch (error) {
            console.error('히스토리 로드 오류:', error);
            historyList.innerHTML = '<p class="error-message">히스토리를 불러오는데 실패했습니다.</p>';
        }
    },

    /**
     * 심층 모니터링 데이터 로드
     */
    async loadDeepMonitoringData(projectId) {
        this.resetDeepMonitoringUI();

        try {
            const response = await fetch(`/api/v1/monitoring/logs/${projectId}/latest?check_type=playwright`, {
                headers: auth.getAuthHeaders()
            });

            if (response.ok) {
                const log = await response.json();
                this.updateDeepMonitoringUI(log);
            } else if (response.status === 404) {
                document.getElementById('detail-dom-ready').innerHTML = '<span class="health-badge unknown">미확인</span>';
                document.getElementById('detail-js-healthy').innerHTML = '<span class="health-badge unknown">미확인</span>';
            }
        } catch (error) {
            console.error('심층 모니터링 데이터 로드 오류:', error);
        }
    },

    /**
     * 심층 모니터링 UI 초기화
     */
    resetDeepMonitoringUI() {
        const fields = [
            'detail-dom-ready', 'detail-js-healthy', 'detail-js-errors',
            'detail-ttfb', 'detail-dom-load-time', 'detail-page-load-time',
            'detail-fcp', 'detail-lcp', 'detail-cls',
            'detail-resource-count', 'detail-failed-resources', 'detail-redirect-count', 'detail-js-heap'
        ];
        fields.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '-';
        });
    },

    /**
     * 심층 모니터링 UI 업데이트
     */
    updateDeepMonitoringUI(data) {
        // DOM 상태
        if (data.is_dom_ready !== null) {
            document.getElementById('detail-dom-ready').innerHTML = data.is_dom_ready
                ? '<span class="health-badge healthy">정상</span>'
                : '<span class="health-badge unhealthy">오류</span>';
        }

        // JS 건강 상태
        if (data.is_js_healthy !== null) {
            document.getElementById('detail-js-healthy').innerHTML = data.is_js_healthy
                ? '<span class="health-badge healthy">정상</span>'
                : '<span class="health-badge unhealthy">에러 발견</span>';
        }

        // JS 에러
        const jsErrors = data.js_errors ? JSON.parse(data.js_errors) : [];
        if (jsErrors.length > 0) {
            let errorsHtml = `<span class="health-badge unhealthy">${jsErrors.length}개</span>`;
            errorsHtml += '<div class="js-error-list">';
            jsErrors.slice(0, 3).forEach(err => {
                errorsHtml += `<div class="js-error-item">${utils.escapeHtml(err.substring(0, 100))}</div>`;
            });
            if (jsErrors.length > 3) {
                errorsHtml += `<div class="js-error-item">... 외 ${jsErrors.length - 3}개</div>`;
            }
            errorsHtml += '</div>';
            document.getElementById('detail-js-errors').innerHTML = errorsHtml;
        } else {
            document.getElementById('detail-js-errors').innerHTML = '<span class="health-badge healthy">없음</span>';
        }

        // 성능 메트릭
        this.updateMetricValue('detail-ttfb', data.time_to_first_byte, 'ms');
        this.updateMetricValue('detail-dom-load-time', data.dom_content_loaded, 'ms');
        this.updateMetricValue('detail-page-load-time', data.page_load_time, 'ms');
        this.updateMetricValue('detail-fcp', data.first_contentful_paint, 'ms');
        this.updateMetricValue('detail-lcp', data.largest_contentful_paint, 'ms');
        this.updateClsValue('detail-cls', data.cumulative_layout_shift);

        // 리소스 & 네트워크
        const resourceCountEl = document.getElementById('detail-resource-count');
        if (resourceCountEl) {
            resourceCountEl.textContent = data.resource_count !== null ? `${data.resource_count}개` : '-';
        }

        const failedEl = document.getElementById('detail-failed-resources');
        if (failedEl && data.failed_resources !== null && data.failed_resources !== undefined) {
            failedEl.textContent = `${data.failed_resources}개`;
            failedEl.className = 'metric-value';
            failedEl.classList.add(data.failed_resources === 0 ? 'good' : 'bad');
        }

        const redirectEl = document.getElementById('detail-redirect-count');
        if (redirectEl) {
            redirectEl.textContent = data.redirect_count !== null ? `${data.redirect_count}회` : '-';
        }

        // JS 메모리
        const heapEl = document.getElementById('detail-js-heap');
        if (heapEl && data.js_heap_size !== null && data.js_heap_size !== undefined) {
            const heapMB = (data.js_heap_size / 1024 / 1024).toFixed(1);
            heapEl.textContent = `${heapMB}MB`;
            heapEl.className = 'metric-value';
            if (data.js_heap_size < 50 * 1024 * 1024) {
                heapEl.classList.add('good');
            } else if (data.js_heap_size < 100 * 1024 * 1024) {
                heapEl.classList.add('warning');
            } else {
                heapEl.classList.add('bad');
            }
        }
    },

    /**
     * 메트릭 값 업데이트
     */
    updateMetricValue(elementId, value, unit) {
        const element = document.getElementById(elementId);
        if (!element) return;

        if (value === null || value === undefined) {
            element.textContent = '-';
            element.className = 'metric-value';
            return;
        }

        const displayValue = Math.round(value);
        element.textContent = `${displayValue}${unit}`;
        element.className = 'metric-value';

        if (displayValue < 1000) {
            element.classList.add('good');
        } else if (displayValue < 3000) {
            element.classList.add('warning');
        } else {
            element.classList.add('bad');
        }
    },

    /**
     * CLS 값 업데이트
     */
    updateClsValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (!element) return;

        if (value === null || value === undefined) {
            element.textContent = '-';
            element.className = 'metric-value';
            return;
        }

        element.textContent = value.toFixed(3);
        element.className = 'metric-value';

        if (value < 0.1) {
            element.classList.add('good');
        } else if (value < 0.25) {
            element.classList.add('warning');
        } else {
            element.classList.add('bad');
        }
    },

    /**
     * 심층 체크 실행
     */
    async runDeepCheck() {
        if (!this.currentProjectId) return;

        const btn = document.getElementById('run-deep-check-btn');
        if (btn) {
            btn.disabled = true;
            btn.textContent = '체크 중...';
        }

        try {
            const response = await fetch(`/api/v1/monitoring/check/deep/${this.currentProjectId}?save_log=true`, {
                headers: auth.getAuthHeaders()
            });

            if (response.ok) {
                const data = await response.json();

                this.updateDeepMonitoringUI({
                    is_dom_ready: data.health.is_dom_ready,
                    is_js_healthy: data.health.is_js_healthy,
                    js_errors: JSON.stringify(data.health.js_errors),
                    time_to_first_byte: data.performance.time_to_first_byte,
                    dom_content_loaded: data.performance.dom_content_loaded,
                    page_load_time: data.performance.page_load_time,
                    first_contentful_paint: data.performance.first_contentful_paint,
                    largest_contentful_paint: data.performance.largest_contentful_paint,
                    cumulative_layout_shift: data.performance.cumulative_layout_shift,
                    resource_count: data.resources.count,
                    failed_resources: data.resources.failed,
                    redirect_count: data.network.redirect_count,
                    js_heap_size: data.memory.js_heap_size
                });

                showToast('심층 체크가 완료되었습니다.', 'success');
            } else {
                const error = await response.json();
                showToast(error.detail || '심층 체크에 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('심층 체크 오류:', error);
            showToast('심층 체크 중 오류가 발생했습니다.', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = '심층 체크 실행';
            }
        }
    }
};

// 전역으로 노출
window.dashboard = dashboard;

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => dashboard.init());
