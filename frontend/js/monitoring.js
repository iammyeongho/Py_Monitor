// 모니터링 관련 함수들
const monitoring = {
    // 모니터링 상태 조회
    async getMonitoringStatus(projectId) {
        try {
            const response = await fetch(`/api/v1/monitoring/${projectId}/status`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });
            
            if (!response.ok) {
                throw new Error('모니터링 상태 조회에 실패했습니다.');
            }
            
            return await response.json();
        } catch (error) {
            console.error('모니터링 상태 조회 오류:', error);
            throw error;
        }
    },
    
    // 모니터링 로그 조회
    async getMonitoringLogs(projectId, page = 1, limit = 10) {
        try {
            const response = await fetch(`/api/v1/monitoring/${projectId}/logs?page=${page}&limit=${limit}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });
            
            if (!response.ok) {
                throw new Error('모니터링 로그 조회에 실패했습니다.');
            }
            
            return await response.json();
        } catch (error) {
            console.error('모니터링 로그 조회 오류:', error);
            throw error;
        }
    },
    
    // 모니터링 설정 업데이트
    async updateMonitoringSettings(projectId, settings) {
        try {
            const response = await fetch(`/api/v1/monitoring/${projectId}/settings`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(settings),
            });
            
            if (!response.ok) {
                throw new Error('모니터링 설정 업데이트에 실패했습니다.');
            }
            
            return await response.json();
        } catch (error) {
            console.error('모니터링 설정 업데이트 오류:', error);
            throw error;
        }
    },
    
    // 모니터링 알림 설정 업데이트
    async updateNotificationSettings(projectId, settings) {
        try {
            const response = await fetch(`/api/v1/monitoring/${projectId}/notifications`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(settings),
            });
            
            if (!response.ok) {
                throw new Error('알림 설정 업데이트에 실패했습니다.');
            }
            
            return await response.json();
        } catch (error) {
            console.error('알림 설정 업데이트 오류:', error);
            throw error;
        }
    },
    
    // 실시간 모니터링 상태 업데이트
    startRealtimeMonitoring(projectId, callback) {
        const ws = new WebSocket(`ws://${window.location.host}/ws/monitoring/${projectId}`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            callback(data);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket 오류:', error);
        };
        
        return ws;
    }
}; 