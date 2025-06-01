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
if (document.getElementById('dashboard')) {
  // 실제로는 API에서 받아와야 함
  const projects = [
    {
      id: 1,
      title: '테스트 서버',
      url: 'https://test.com',
      status: 'ok',
      statusText: '정상',
      interval: 60,
      snapshot: 'https://via.placeholder.com/400x300?text=Test+Server',
      sslStatus: '유효',
      sslExpiry: '2025-12-31',
      domainExpiry: '2025-01-15',
      jsMetrics: 'A+ (98점)'
    },
    {
      id: 2,
      title: 'API 서버',
      url: 'https://api.com',
      status: 'error',
      statusText: '오류',
      interval: 30,
      snapshot: 'https://via.placeholder.com/400x300?text=API+Server',
      sslStatus: '만료',
      sslExpiry: '2025-03-01',
      domainExpiry: '2025-12-31',
      jsMetrics: 'B (85점)'
    },
    {
      id: 3,
      title: 'DB 서버',
      url: 'https://db.com',
      status: 'warn',
      statusText: '느림',
      interval: 120,
      snapshot: 'https://via.placeholder.com/400x300?text=DB+Server',
      sslStatus: '없음',
      sslExpiry: null,
      domainExpiry: '2025-06-30',
      jsMetrics: 'A (92점)'
    }
  ];
  const dashboard = document.getElementById('dashboard');
  dashboard.innerHTML = projects.map(p => `
    <div class="card">
      <div class="snapshot-container">
        <img src="${p.snapshot}" alt="${p.title} 스냅샷">
        <div class="snapshot-overlay">
          <span class="status ${p.status}">${p.statusText}</span>
        </div>
      </div>
      <div class="card-content">
        <h3>${p.title}</h3>
        <button onclick="openDetailModal(${p.id})" class="detail-btn">상세보기</button>
      </div>
    </div>
  `).join('');
}

// --- 프로젝트 등록/수정 폼 제출 (예시) ---
if (document.getElementById('project-form')) {
  document.getElementById('project-form').onsubmit = function(e) {
    e.preventDefault();
    // 실제로는 fetch로 API 호출
    alert('프로젝트가 저장되었습니다! (실제 저장은 API 연동 필요)');
    window.location.href = 'index.html';
  };
}

// --- 로그인/회원가입 폼 제출 (예시) ---
if (document.getElementById('login-form')) {
  document.getElementById('login-form').onsubmit = function(e) {
    e.preventDefault();
    // 실제로는 fetch로 API 호출
    alert('로그인 성공! (실제 인증은 API 연동 필요)');
    window.location.href = 'index.html';
  };
}
if (document.getElementById('register-form')) {
  document.getElementById('register-form').onsubmit = function(e) {
    e.preventDefault();
    // 실제로는 fetch로 API 호출
    alert('회원가입 성공! (실제 저장은 API 연동 필요)');
    window.location.href = 'login.html';
  };
}

// API 엔드포인트
const API_BASE_URL = 'http://localhost:8000/api';

// 모니터링 로그 관련 함수
async function getMonitoringLogs(projectId) {
    try {
        const response = await fetch(`${API_BASE_URL}/monitoring/logs/${projectId}`);
        if (!response.ok) throw new Error('Failed to fetch monitoring logs');
        return await response.json();
    } catch (error) {
        console.error('Error fetching monitoring logs:', error);
        return [];
    }
}

// 모니터링 알림 관련 함수
async function getMonitoringAlerts(projectId) {
    try {
        const response = await fetch(`${API_BASE_URL}/monitoring/alerts/${projectId}`);
        if (!response.ok) throw new Error('Failed to fetch monitoring alerts');
        return await response.json();
    } catch (error) {
        console.error('Error fetching monitoring alerts:', error);
        return [];
    }
}

async function updateAlertStatus(alertId, isResolved) {
    try {
        const response = await fetch(`${API_BASE_URL}/monitoring/alerts/${alertId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                is_resolved: isResolved,
                resolved_at: isResolved ? new Date().toISOString() : null
            })
        });
        if (!response.ok) throw new Error('Failed to update alert status');
        return await response.json();
    } catch (error) {
        console.error('Error updating alert status:', error);
        return null;
    }
}

// 모니터링 설정 관련 함수
async function getMonitoringSettings(projectId) {
    try {
        const response = await fetch(`${API_BASE_URL}/monitoring/settings/${projectId}`);
        if (!response.ok) throw new Error('Failed to fetch monitoring settings');
        return await response.json();
    } catch (error) {
        console.error('Error fetching monitoring settings:', error);
        return null;
    }
}

async function updateMonitoringSettings(settingId, settings) {
    try {
        const response = await fetch(`${API_BASE_URL}/monitoring/settings/${settingId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings)
        });
        if (!response.ok) throw new Error('Failed to update monitoring settings');
        return await response.json();
    } catch (error) {
        console.error('Error updating monitoring settings:', error);
        return null;
    }
}

// 대시보드 업데이트 함수
async function updateDashboard() {
    const projects = await getProjects();
    const dashboard = document.getElementById('dashboard');
    
    if (!dashboard) return;
    
    dashboard.innerHTML = await Promise.all(projects.map(async project => {
        const settings = await getMonitoringSettings(project.id);
        const alerts = await getMonitoringAlerts(project.id);
        const logs = await getMonitoringLogs(project.id);
        
        const latestLog = logs[0];
        const unresolvedAlerts = alerts.filter(alert => !alert.is_resolved);
        
        return `
            <div class="card">
                <div class="snapshot-container">
                    <img src="${project.snapshot_path || 'https://via.placeholder.com/400x300?text=No+Snapshot'}" 
                         alt="${project.title} snapshot">
                    <div class="status-indicator ${latestLog?.is_available ? 'ok' : 'error'}">
                        ${latestLog?.is_available ? '정상' : '오류'}
                    </div>
                </div>
                <div class="card-content">
                    <h3>${project.title}</h3>
                    <p class="url">${project.url}</p>
                    <div class="info-badges">
                        <span class="badge ssl ${project.ssl_status}">SSL: ${project.ssl_status}</span>
                        <span class="badge expiry">만료: ${project.expiry_d_day}일</span>
                        <span class="badge metrics">JS: ${project.js_metrics}</span>
                    </div>
                    <div class="alert-count">
                        미해결 알림: ${unresolvedAlerts.length}개
                    </div>
                    <div class="monitoring-info">
                        <p>체크 주기: ${settings?.check_interval || 60}초</p>
                        <p>응답 시간: ${latestLog?.response_time || 'N/A'}초</p>
                    </div>
                </div>
                <div class="card-actions">
                    <button onclick="openDetailModal(${project.id})" class="btn-detail">상세 정보</button>
                    <button onclick="openModal(${project.id})" class="btn-setting">설정</button>
                </div>
            </div>
        `;
    })).join('');
}

// 상세 정보 모달 업데이트
async function updateDetailModal(projectId) {
    const project = await getProject(projectId);
    const settings = await getMonitoringSettings(projectId);
    const alerts = await getMonitoringAlerts(projectId);
    const logs = await getMonitoringLogs(projectId);
    
    const detailContent = document.getElementById('detail-content');
    if (!detailContent) return;
    
    detailContent.innerHTML = `
        <div class="detail-section">
            <h4>기본 정보</h4>
            <p>URL: ${project.url}</p>
            <p>SSL 상태: ${project.ssl_status}</p>
            <p>도메인 만료일: ${project.expiry_d_day}일</p>
            <p>JS 메트릭스: ${project.js_metrics}</p>
        </div>
        
        <div class="detail-section">
            <h4>모니터링 설정</h4>
            <p>체크 주기: ${settings?.check_interval || 60}초</p>
            <p>타임아웃: ${settings?.timeout || 30}초</p>
            <p>재시도 횟수: ${settings?.retry_count || 3}회</p>
            <p>알림 임계값: ${settings?.alert_threshold || 3}회</p>
        </div>
        
        <div class="detail-section">
            <h4>최근 로그</h4>
            <div class="log-list">
                ${logs.slice(0, 5).map(log => `
                    <div class="log-item ${log.is_available ? 'ok' : 'error'}">
                        <span class="time">${new Date(log.created_at).toLocaleString()}</span>
                        <span class="status">${log.is_available ? '정상' : '오류'}</span>
                        <span class="response-time">${log.response_time}초</span>
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="detail-section">
            <h4>미해결 알림</h4>
            <div class="alert-list">
                ${alerts.filter(alert => !alert.is_resolved).map(alert => `
                    <div class="alert-item">
                        <span class="type">${alert.alert_type}</span>
                        <span class="message">${alert.message}</span>
                        <button onclick="resolveAlert(${alert.id})" class="btn-resolve">해결</button>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// 알림 해결 처리
async function resolveAlert(alertId) {
    const result = await updateAlertStatus(alertId, true);
    if (result) {
        const projectId = result.project_id;
        updateDetailModal(projectId);
        updateDashboard();
    }
}

// 페이지 로드 시 대시보드 업데이트
document.addEventListener('DOMContentLoaded', () => {
    updateDashboard();
    // 1분마다 대시보드 자동 업데이트
    setInterval(updateDashboard, 60000);
});
