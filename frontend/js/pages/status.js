/**
 * PyMonitor - 공개 상태 페이지 모듈
 * 인증 없이 접근 가능한 공개 상태 페이지
 */

const statusPage = {
    currentView: 'list', // 'list' or 'detail'
    data: null,

    /**
     * 초기화
     */
    init() {
        // URL 파라미터로 프로젝트 ID가 있으면 상세 뷰
        const params = new URLSearchParams(window.location.search);
        const projectId = params.get('project');
        if (projectId) {
            this.showDetail(parseInt(projectId));
        } else {
            this.loadStatusList();
        }
    },

    /**
     * 상태 목록 로드
     */
    async loadStatusList() {
        const container = document.getElementById('status-content');
        container.innerHTML = '<div class="status-loading">상태 정보를 불러오는 중...</div>';

        try {
            const response = await fetch('/api/v1/status/');
            if (!response.ok) throw new Error('상태 정보를 불러올 수 없습니다');

            this.data = await response.json();
            this.renderStatusList();
        } catch (error) {
            console.error('상태 페이지 로드 오류:', error);
            container.innerHTML = `
                <div class="status-empty">
                    <div class="status-empty-icon">!</div>
                    <div class="status-empty-text">상태 정보를 불러올 수 없습니다</div>
                </div>
            `;
        }
    },

    /**
     * 상태 목록 렌더링
     */
    renderStatusList() {
        const container = document.getElementById('status-content');
        const { overall_status, projects, last_updated } = this.data;

        const statusMap = {
            operational: { text: '모든 시스템 정상 운영 중', icon: '&#10003;' },
            degraded: { text: '일부 시스템 성능 저하', icon: '!' },
            major_outage: { text: '주요 시스템 장애 발생', icon: '&#10007;' },
        };

        const status = statusMap[overall_status] || statusMap.operational;
        const updatedTime = last_updated ? new Date(last_updated).toLocaleString('ko-KR') : '-';

        let projectsHtml = '';
        if (projects.length === 0) {
            projectsHtml = `
                <div class="status-empty">
                    <div class="status-empty-text">공개된 모니터링 프로젝트가 없습니다</div>
                </div>
            `;
        } else {
            projectsHtml = '<div class="status-list">';
            for (const project of projects) {
                const indicatorClass = project.is_available ? 'up' : 'down';
                const uptimeClass = this.getUptimeClass(project.uptime_24h);
                const responseText = project.response_time
                    ? `${(project.response_time * 1000).toFixed(0)}ms`
                    : '-';
                const statusBadge = project.is_available
                    ? '<span class="status-text-badge up">정상</span>'
                    : '<span class="status-text-badge down">장애</span>';

                projectsHtml += `
                    <div class="status-item" data-project-id="${project.id}" onclick="statusPage.showDetail(${project.id})">
                        <div class="status-item-left">
                            <div class="status-indicator ${indicatorClass}"></div>
                            <div class="status-item-info">
                                <div class="status-item-title">${this.escapeHtml(project.title)}</div>
                                <div class="status-item-url">${this.escapeHtml(project.url)}</div>
                            </div>
                        </div>
                        <div class="status-item-right">
                            <div class="status-item-uptime">
                                <div class="status-item-uptime-value ${uptimeClass}">${project.uptime_24h}%</div>
                                <div class="status-item-uptime-label">24시간 가용률</div>
                            </div>
                            <div class="status-item-response">
                                <div class="status-item-response-value">${responseText}</div>
                                <div class="status-item-response-label">응답 시간</div>
                            </div>
                            ${statusBadge}
                        </div>
                    </div>
                `;
            }
            projectsHtml += '</div>';
        }

        container.innerHTML = `
            <div class="status-banner ${overall_status}">
                <div class="status-banner-icon">${status.icon}</div>
                <div class="status-banner-text">${status.text}</div>
                <div class="status-banner-time">마지막 업데이트: ${updatedTime}</div>
            </div>
            ${projectsHtml}
        `;

        this.currentView = 'list';
        this.updateUrl(null);
    },

    /**
     * 프로젝트 상세 상태 표시
     */
    async showDetail(projectId) {
        const container = document.getElementById('status-content');
        container.innerHTML = '<div class="status-loading">상세 정보를 불러오는 중...</div>';

        try {
            const response = await fetch(`/api/v1/status/${projectId}?days=90`);
            if (!response.ok) throw new Error('프로젝트 정보를 불러올 수 없습니다');

            const detail = await response.json();
            this.renderDetail(detail);
            this.updateUrl(projectId);
        } catch (error) {
            console.error('상세 상태 로드 오류:', error);
            container.innerHTML = `
                <div class="status-empty">
                    <div class="status-empty-text">프로젝트 정보를 불러올 수 없습니다</div>
                </div>
            `;
        }
    },

    /**
     * 상세 뷰 렌더링
     */
    renderDetail(detail) {
        const container = document.getElementById('status-content');

        const uptimeClass24 = this.getUptimeClass(detail.uptime_24h);
        const uptimeClass7 = this.getUptimeClass(detail.uptime_7d);
        const uptimeClass30 = this.getUptimeClass(detail.uptime_30d);
        const uptimeClass90 = this.getUptimeClass(detail.uptime_90d);

        const responseText = detail.response_time
            ? `${(detail.response_time * 1000).toFixed(0)}ms`
            : '-';
        const avgResponseText = detail.avg_response_time
            ? `${(detail.avg_response_time * 1000).toFixed(0)}ms`
            : '-';

        // 90일 uptime 바 차트
        let uptimeBarsHtml = '';
        const dailyUptime = detail.daily_uptime || [];
        for (const day of dailyUptime) {
            let barClass = 'good';
            if (day.total_checks === 0) barClass = 'empty';
            else if (day.uptime_percentage < 90) barClass = 'bad';
            else if (day.uptime_percentage < 99) barClass = 'warn';

            uptimeBarsHtml += `
                <div class="uptime-bar ${barClass}" style="height: 100%;">
                    <div class="uptime-bar-tooltip">${day.date}: ${day.uptime_percentage}% (${day.available_checks}/${day.total_checks})</div>
                </div>
            `;
        }

        const firstDate = dailyUptime.length > 0 ? dailyUptime[0].date : '';
        const lastDate = dailyUptime.length > 0 ? dailyUptime[dailyUptime.length - 1].date : '';

        // 인시던트 목록
        let incidentsHtml = '';
        if (detail.recent_incidents && detail.recent_incidents.length > 0) {
            for (const incident of detail.recent_incidents) {
                const time = new Date(incident.timestamp).toLocaleString('ko-KR');
                const msg = incident.error_message || `HTTP ${incident.status_code || 'N/A'}`;
                incidentsHtml += `
                    <div class="incident-item">
                        <div class="incident-dot"></div>
                        <div class="incident-info">
                            <div class="incident-time">${time}</div>
                            <div class="incident-message">${this.escapeHtml(msg)}</div>
                        </div>
                    </div>
                `;
            }
        } else {
            incidentsHtml = '<div class="incidents-empty">최근 90일간 장애가 없습니다</div>';
        }

        container.innerHTML = `
            <div class="status-detail">
                <div class="status-detail-header">
                    <button class="status-detail-back" onclick="statusPage.goBack()">&#8592; 목록으로</button>
                    <h1 class="status-detail-title">${this.escapeHtml(detail.title)}</h1>
                </div>

                <div class="status-stats">
                    <div class="status-stat-card">
                        <div class="status-stat-value ${detail.is_available ? 'good' : 'bad'}">
                            ${detail.is_available ? '정상' : '장애'}
                        </div>
                        <div class="status-stat-label">현재 상태</div>
                    </div>
                    <div class="status-stat-card">
                        <div class="status-stat-value">${responseText}</div>
                        <div class="status-stat-label">현재 응답 시간</div>
                    </div>
                    <div class="status-stat-card">
                        <div class="status-stat-value">${avgResponseText}</div>
                        <div class="status-stat-label">24시간 평균</div>
                    </div>
                    <div class="status-stat-card">
                        <div class="status-stat-value ${uptimeClass24}">${detail.uptime_24h}%</div>
                        <div class="status-stat-label">24시간 가용률</div>
                    </div>
                    <div class="status-stat-card">
                        <div class="status-stat-value ${uptimeClass7}">${detail.uptime_7d}%</div>
                        <div class="status-stat-label">7일 가용률</div>
                    </div>
                    <div class="status-stat-card">
                        <div class="status-stat-value ${uptimeClass30}">${detail.uptime_30d}%</div>
                        <div class="status-stat-label">30일 가용률</div>
                    </div>
                </div>

                <div class="uptime-chart">
                    <div class="uptime-chart-title">90일 가용률 이력</div>
                    <div class="uptime-bars">
                        ${uptimeBarsHtml}
                    </div>
                    <div class="uptime-chart-labels">
                        <span>${firstDate}</span>
                        <span>${lastDate}</span>
                    </div>
                </div>

                <div class="incidents-section">
                    <div class="incidents-title">최근 장애 이력</div>
                    ${incidentsHtml}
                </div>
            </div>
        `;

        this.currentView = 'detail';
    },

    /**
     * 목록으로 돌아가기
     */
    goBack() {
        if (this.data) {
            this.renderStatusList();
        } else {
            this.loadStatusList();
        }
    },

    /**
     * URL 업데이트 (히스토리 API)
     */
    updateUrl(projectId) {
        const url = projectId
            ? `${window.location.pathname}?project=${projectId}`
            : window.location.pathname;
        window.history.replaceState(null, '', url);
    },

    /**
     * Uptime 값에 따른 CSS 클래스
     */
    getUptimeClass(uptime) {
        if (uptime >= 99) return 'good';
        if (uptime >= 95) return 'warn';
        return 'bad';
    },

    /**
     * HTML 이스케이프
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// 전역으로 노출
window.statusPage = statusPage;

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => statusPage.init());
