// 모니터링 관련 함수들
const monitoring = {
    // 모니터링 상태 조회
    async getMonitoringStatus(projectId) {
        try {
            const response = await fetch(`/api/v1/monitoring/status/${projectId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '모니터링 상태 조회에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('모니터링 상태 조회 오류:', error);
            throw error;
        }
    },

    // 모든 프로젝트 상태 조회
    async getAllProjectsStatus() {
        try {
            const response = await fetch('/api/v1/monitoring/status', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '모니터링 상태 조회에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('모니터링 상태 조회 오류:', error);
            throw error;
        }
    },

    // 모니터링 설정 조회
    async getSettings(projectId) {
        try {
            const response = await fetch(`/api/v1/monitoring/settings/${projectId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '모니터링 설정 조회에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('모니터링 설정 조회 오류:', error);
            throw error;
        }
    },

    // 모니터링 설정 생성
    async createSettings(projectId, settings) {
        try {
            const response = await fetch('/api/v1/monitoring/settings', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_id: projectId,
                    ...settings
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '모니터링 설정 생성에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('모니터링 설정 생성 오류:', error);
            throw error;
        }
    },

    // 모니터링 설정 업데이트
    async updateSettings(projectId, settings) {
        try {
            const response = await fetch(`/api/v1/monitoring/settings/${projectId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(settings),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '모니터링 설정 업데이트에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('모니터링 설정 업데이트 오류:', error);
            throw error;
        }
    },

    // SSL 상태 조회
    async getSSLStatus(projectId) {
        try {
            const response = await fetch(`/api/v1/monitoring/ssl/${projectId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'SSL 상태 조회에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('SSL 상태 조회 오류:', error);
            throw error;
        }
    },

    // TCP 포트 체크
    async checkTCPPort(host, port, timeout = 5) {
        try {
            const response = await fetch('/api/v1/monitoring/check/tcp', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ host, port, timeout }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'TCP 포트 체크에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('TCP 포트 체크 오류:', error);
            throw error;
        }
    },

    // UDP 포트 체크
    async checkUDPPort(host, port, timeout = 5) {
        try {
            const response = await fetch('/api/v1/monitoring/check/udp', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ host, port, timeout }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'UDP 포트 체크에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('UDP 포트 체크 오류:', error);
            throw error;
        }
    },

    // DNS 조회
    async checkDNS(domain, recordType = 'A') {
        try {
            const response = await fetch('/api/v1/monitoring/check/dns', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ domain, record_type: recordType }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'DNS 조회에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('DNS 조회 오류:', error);
            throw error;
        }
    },

    // 콘텐츠 체크
    async checkContent(url, expectedContent, timeout = 10) {
        try {
            const response = await fetch('/api/v1/monitoring/check/content', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url, expected_content: expectedContent, timeout }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '콘텐츠 체크에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('콘텐츠 체크 오류:', error);
            throw error;
        }
    },

    // API 엔드포인트 체크
    async checkAPIEndpoint(params) {
        try {
            const response = await fetch('/api/v1/monitoring/check/api', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'API 엔드포인트 체크에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('API 엔드포인트 체크 오류:', error);
            throw error;
        }
    },

    // 보안 헤더 체크
    async checkSecurityHeaders(url, timeout = 10) {
        try {
            const response = await fetch('/api/v1/monitoring/check/security-headers', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url, timeout }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '보안 헤더 체크에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('보안 헤더 체크 오류:', error);
            throw error;
        }
    },

    // 실시간 모니터링 상태 업데이트 (WebSocket)
    startRealtimeMonitoring(projectId, callback) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocol}//${window.location.host}/ws/monitoring/${projectId}`);

        ws.onopen = () => {
            console.log('WebSocket 연결됨');
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            callback(data);
        };

        ws.onerror = (error) => {
            console.error('WebSocket 오류:', error);
        };

        ws.onclose = () => {
            console.log('WebSocket 연결 종료');
        };

        return ws;
    },

    // 모니터링 로그 조회
    async getLogs(projectId, skip = 0, limit = 100) {
        try {
            const response = await fetch(`/api/v1/monitoring/logs/${projectId}?skip=${skip}&limit=${limit}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '모니터링 로그 조회에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('모니터링 로그 조회 오류:', error);
            throw error;
        }
    },

    // 모니터링 알림 조회
    async getAlerts(projectId, skip = 0, limit = 50) {
        try {
            const response = await fetch(`/api/v1/monitoring/alerts/${projectId}?skip=${skip}&limit=${limit}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '모니터링 알림 조회에 실패했습니다.');
            }

            return await response.json();
        } catch (error) {
            console.error('모니터링 알림 조회 오류:', error);
            throw error;
        }
    }
};
