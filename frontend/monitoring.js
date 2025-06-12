// monitoring.js

// --- 모니터링 주기 설정 팝업 열기/닫기 ---
function openModal() {
  document.getElementById('setting-modal').style.display = 'flex';
}
function closeModal() {
  document.getElementById('setting-modal').style.display = 'none';
}

// --- 상세 정보 팝업 열기/닫기 ---
function openDetailModal(projectId) {
  document.getElementById('detail-modal').style.display = 'flex';
  const project = projects.find(p => p.id === projectId);
  if (project) {
    // 기본 정보
    document.getElementById('detail-title').textContent = project.title;
    document.getElementById('detail-url').textContent = project.url;
    
    // SSL 정보
    document.getElementById('detail-ssl-status').textContent = project.sslStatus;
    document.getElementById('detail-ssl-expiry').textContent = project.sslExpiry || '없음';
    
    // 도메인 정보
    document.getElementById('detail-domain-expiry').textContent = project.domainExpiry;
    
    // JS 매트릭
    document.getElementById('detail-js-metrics').textContent = project.jsMetrics;
    
    // 모니터링 설정
    document.getElementById('detail-check-interval').value = project.interval;
    document.getElementById('detail-timeout').value = project.timeout || 30;
    document.getElementById('detail-retry-count').value = project.retryCount || 3;
    document.getElementById('detail-alert-threshold').value = project.alertThreshold || 3;

    // 폼 제출 이벤트 설정
    const form = document.getElementById('detail-setting-form');
    form.onsubmit = function(e) {
      e.preventDefault();
      // TODO: API 호출로 설정 저장
      const newSettings = {
        interval: parseInt(document.getElementById('detail-check-interval').value),
        timeout: parseInt(document.getElementById('detail-timeout').value),
        retryCount: parseInt(document.getElementById('detail-retry-count').value),
        alertThreshold: parseInt(document.getElementById('detail-alert-threshold').value)
      };
      console.log('설정 저장:', newSettings);
      alert('설정이 저장되었습니다.');
    };
  }
}
function closeDetailModal() {
  document.getElementById('detail-modal').style.display = 'none';
}

// 버튼 이벤트 연결
window.addEventListener('DOMContentLoaded', function() {
  const openBtn = document.getElementById('open-setting');
  const closeBtn = document.getElementById('close-modal');
  const closeDetailBtn = document.getElementById('close-detail-modal');
  if (openBtn) openBtn.onclick = openModal;
  if (closeBtn) closeBtn.onclick = closeModal;
  if (closeDetailBtn) closeDetailBtn.onclick = closeDetailModal;
});

// --- 대시보드: 프로젝트 카드 렌더링 (예시 데이터) ---
// (예시 데이터 제거)
// 실제로는 API에서 받아와야 함

// --- 프로젝트 등록/수정 폼 제출 (예시) ---
if (document.getElementById('project-form')) {
  document.getElementById('project-form').onsubmit = function(e) {
    e.preventDefault();
    // TODO: 실제로는 fetch로 API 호출하여 프로젝트를 저장해야 합니다.
    // alert('프로젝트가 저장되었습니다! (실제 저장은 API 연동 필요)');
    // window.location.href = 'index.html';
  };
}

// --- 로그인/회원가입 폼 제출 (예시) ---
if (document.getElementById('login-form')) {
  document.getElementById('login-form').onsubmit = function(e) {
    e.preventDefault();
    // TODO: 실제로는 fetch로 API 호출하여 인증해야 합니다.
    // alert('로그인 성공! (실제 인증은 API 연동 필요)');
    // window.location.href = 'index.html';
  };
}
if (document.getElementById('register-form')) {
  document.getElementById('register-form').onsubmit = function(e) {
    e.preventDefault();
    // TODO: 실제로는 fetch로 API 호출하여 회원가입을 처리해야 합니다.
    // alert('회원가입 성공! (실제 저장은 API 연동 필요)');
    // window.location.href = 'login.html';
  };
}

// API 엔드포인트
const API_BASE_URL = 'http://localhost:8000/api';

// 인증 토큰 관리
function getAuthToken() {
    return localStorage.getItem('auth_token');
}

function setAuthToken(token) {
    localStorage.setItem('auth_token', token);
}

function removeAuthToken() {
    localStorage.removeItem('auth_token');
}

// API 요청 헬퍼 함수
async function apiRequest(endpoint, options = {}) {
    const token = getAuthToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // 인증 실패 시 로그인 페이지로 리다이렉트
            removeAuthToken();
            window.location.href = '/login.html';
            return null;
        }

        if (!response.ok) {
            throw new Error(`API request failed: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// 프로젝트 관련 함수
async function getProjects() {
    try {
        return await apiRequest('/monitoring/projects');
    } catch (error) {
        console.error('Error fetching projects:', error);
        return [];
    }
}

async function createProject(projectData) {
    try {
        return await apiRequest('/monitoring/projects', {
            method: 'POST',
            body: JSON.stringify(projectData)
        });
    } catch (error) {
        console.error('Error creating project:', error);
        throw error;
    }
}

// 모니터링 로그 관련 함수
async function getMonitoringLogs(projectId) {
    try {
        return await apiRequest(`/monitoring/logs/${projectId}`);
    } catch (error) {
        console.error('Error fetching monitoring logs:', error);
        return [];
    }
}

// 모니터링 알림 관련 함수
async function getMonitoringAlerts(projectId, isResolved = null) {
    try {
        const queryParams = isResolved !== null ? `?is_resolved=${isResolved}` : '';
        return await apiRequest(`/monitoring/alerts/${projectId}${queryParams}`);
    } catch (error) {
        console.error('Error fetching monitoring alerts:', error);
        return [];
    }
}

async function updateAlertStatus(alertId, isResolved) {
    try {
        return await apiRequest(`/monitoring/alerts/${alertId}`, {
            method: 'PUT',
            body: JSON.stringify({ is_resolved: isResolved })
        });
    } catch (error) {
        console.error('Error updating alert status:', error);
        throw error;
    }
}

// 모니터링 설정 관련 함수
async function getMonitoringSettings(projectId) {
    try {
        return await apiRequest(`/monitoring/settings/${projectId}`);
    } catch (error) {
        console.error('Error fetching monitoring settings:', error);
        return null;
    }
}

async function updateMonitoringSettings(projectId, settings) {
    try {
        const response = await fetch(`${API_BASE_URL}/monitoring/settings/${projectId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(settings)
        });
        
        if (response.ok) {
            showNotification("모니터링 설정이 업데이트되었습니다.");
        }
    } catch (error) {
        console.error("Error updating monitoring settings:", error);
        showNotification("모니터링 설정 업데이트에 실패했습니다.", "error");
    }
}

// 대시보드 업데이트 함수
async function updateDashboard() {
    try {
        const projects = await getProjects();
        const dashboard = document.getElementById('dashboard');
        
        if (!dashboard) return;
        
        let html = '';
        for (const p of projects) {
            const alerts = await getMonitoringAlerts(p.id, false);
            html += `
                <div class="card">
                    <div class="snapshot-container">
                        <img src="${p.snapshot_path || 'https://via.placeholder.com/400x300?text=No+Snapshot'}" 
                             alt="${p.title} snapshot">
                        <div class="snapshot-overlay">
                            <span class="status ${p.status}">${p.status_text}</span>
                        </div>
                    </div>
                    <div class="card-content">
                        <h3>${p.title}</h3>
                        <p>${p.url}</p>
                        <div class="metrics">
                            <span class="metric ${p.ssl_status === '유효' ? 'ok' : 'error'}">
                                SSL: ${p.ssl_status}
                            </span>
                            <span class="metric">
                                알림: ${alerts.length}개
                            </span>
                        </div>
                        <button onclick="openDetailModal(${p.id})" class="detail-btn">상세보기</button>
                    </div>
                </div>
            `;
        }
        dashboard.innerHTML = html;
    } catch (error) {
        console.error('Error updating dashboard:', error);
    }
}

// 상세 모달 업데이트 함수
async function updateDetailModal(projectId) {
    try {
        const project = (await getProjects()).find(p => p.id === projectId);
        if (!project) return;

        const settings = await getMonitoringSettings(project.id);
        const alerts = await getMonitoringAlerts(project.id);
        const logs = await getMonitoringLogs(project.id);

        // 기본 정보 업데이트
        document.getElementById('detail-title').textContent = project.title;
        document.getElementById('detail-url').textContent = project.url;
        
        // SSL 정보 업데이트
        document.getElementById('detail-ssl-status').textContent = project.ssl_status;
        document.getElementById('detail-ssl-expiry').textContent = project.ssl_expiry || '없음';
        
        // 도메인 정보 업데이트
        document.getElementById('detail-domain-expiry').textContent = project.domain_expiry;
        
        // JS 매트릭 업데이트
        document.getElementById('detail-js-metrics').textContent = project.js_metrics;
        
        // 모니터링 설정 업데이트
        if (settings) {
            document.getElementById('detail-check-interval').value = settings.check_interval;
            document.getElementById('detail-timeout').value = settings.timeout;
            document.getElementById('detail-retry-count').value = settings.retry_count;
            document.getElementById('detail-response-limit').value = settings.response_limit;
            document.getElementById('detail-response-alert-interval').value = settings.response_alert_interval;
            document.getElementById('detail-error-alert-interval').value = settings.error_alert_interval;
            document.getElementById('detail-expiry-dday').value = settings.expiry_dday;
            document.getElementById('detail-expiry-alert-interval').value = settings.expiry_alert_interval;
        }

        // 폼 제출 이벤트 설정
        const form = document.getElementById('detail-setting-form');
        form.onsubmit = async function(e) {
            e.preventDefault();
            try {
                const newSettings = {
                    check_interval: parseInt(document.getElementById('detail-check-interval').value),
                    timeout: parseInt(document.getElementById('detail-timeout').value),
                    retry_count: parseInt(document.getElementById('detail-retry-count').value),
                    response_limit: parseInt(document.getElementById('detail-response-limit').value),
                    response_alert_interval: parseInt(document.getElementById('detail-response-alert-interval').value),
                    error_alert_interval: parseInt(document.getElementById('detail-error-alert-interval').value),
                    expiry_dday: parseInt(document.getElementById('detail-expiry-dday').value),
                    expiry_alert_interval: parseInt(document.getElementById('detail-expiry-alert-interval').value)
                };

                await updateMonitoringSettings(projectId, newSettings);
                alert('설정이 저장되었습니다.');
            } catch (error) {
                console.error('Error saving settings:', error);
                alert('설정 저장 중 오류가 발생했습니다.');
            }
        };
    } catch (error) {
        console.error('Error updating detail modal:', error);
    }
}

// 알림 해결 함수
async function resolveAlert(alertId) {
    try {
        const response = await fetch(`${API_BASE_URL}/monitoring/alerts/${alertId}/resolve`, {
            method: "POST"
        });
        
        if (response.ok) {
            const projectId = document.querySelector(".project-card.active").id.split("-")[1];
            await updateAlerts(projectId);
        }
    } catch (error) {
        console.error("Error resolving alert:", error);
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', async () => {
    // 대시보드가 있는 경우 업데이트
    if (document.getElementById('dashboard')) {
        await updateDashboard();
        // 1분마다 대시보드 업데이트
        setInterval(updateDashboard, 60000);
    }

    // 모달 닫기 버튼 이벤트 설정
    const closeModalBtn = document.getElementById('close-modal');
    const closeDetailModalBtn = document.getElementById('close-detail-modal');
    if (closeModalBtn) closeModalBtn.onclick = closeModal;
    if (closeDetailModalBtn) closeDetailModalBtn.onclick = closeDetailModal;
});

// 모니터링 상태 업데이트 함수
async function updateMonitoringStatus(projectId) {
    try {
        const response = await fetch(`${API_BASE_URL}/monitoring/status/${projectId}`);
        const data = await response.json();
        
        const statusElement = document.querySelector(`#project-${projectId} .status`);
        const responseTimeElement = document.querySelector(`#project-${projectId} .response-time`);
        
        if (data.is_available) {
            statusElement.textContent = "정상";
            statusElement.className = "status available";
        } else {
            statusElement.textContent = "오류";
            statusElement.className = "status error";
        }
        
        if (data.response_time) {
            responseTimeElement.textContent = `${data.response_time.toFixed(2)}ms`;
        }
    } catch (error) {
        console.error("Error updating monitoring status:", error);
    }
}

// 알림 목록 업데이트 함수
async function updateAlerts(projectId) {
    try {
        const response = await fetch(`${API_BASE_URL}/monitoring/alerts/${projectId}`);
        const alerts = await response.json();
        
        const alertsContainer = document.querySelector(`#project-${projectId} .alerts`);
        alertsContainer.innerHTML = "";
        
        alerts.forEach(alert => {
            const alertElement = document.createElement("div");
            alertElement.className = `alert ${alert.alert_type}`;
            alertElement.innerHTML = `
                <div class="alert-header">
                    <span class="alert-type">${getAlertTypeLabel(alert.alert_type)}</span>
                    <span class="alert-time">${formatDate(alert.created_at)}</span>
                </div>
                <div class="alert-message">${alert.message}</div>
                ${alert.is_resolved ? 
                    `<div class="alert-resolved">해결됨</div>` : 
                    `<button onclick="resolveAlert(${alert.id})" class="resolve-btn">해결</button>`
                }
            `;
            alertsContainer.appendChild(alertElement);
        });
    } catch (error) {
        console.error("Error updating alerts:", error);
    }
}

// 알림 타입 레이블 변환 함수
function getAlertTypeLabel(type) {
    const labels = {
        "status_error": "상태 오류",
        "ssl_error": "SSL 오류",
        "domain_expiry": "도메인 만료",
        "monitoring_error": "모니터링 오류"
    };
    return labels[type] || type;
}

// 알림 표시 함수
function showNotification(message, type = "success") {
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add("show");
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove("show");
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// 날짜 포맷 함수
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString("ko-KR", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
    });
}

// 프로젝트 카드 렌더링 함수 개선
function renderProjectCard(project) {
    return `
        <div class="project-card" id="project-${project.id}">
            <div class="project-header">
                <h3>${project.title}</h3>
                <div class="project-actions">
                    <button onclick="openSettingsModal(${project.id})" class="settings-btn">
                        <i class="fas fa-cog"></i>
                    </button>
                    <button onclick="toggleMonitoring(${project.id})" class="monitoring-btn">
                        <i class="fas fa-${project.is_active ? 'pause' : 'play'}"></i>
                    </button>
                </div>
            </div>
            <div class="project-status">
                <div class="status-indicator">
                    <span class="status">확인 중...</span>
                    <span class="response-time">-</span>
                </div>
                <div class="ssl-status">
                    <i class="fas fa-lock"></i>
                    <span>SSL 확인 중...</span>
                </div>
            </div>
            <div class="project-details">
                <div class="detail-item">
                    <i class="fas fa-link"></i>
                    <span>${project.url}</span>
                </div>
                <div class="detail-item">
                    <i class="fas fa-clock"></i>
                    <span>체크 간격: ${project.check_interval}초</span>
                </div>
            </div>
            <div class="alerts"></div>
        </div>
    `;
}
