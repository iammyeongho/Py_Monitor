// Jest를 사용한 프론트엔드 테스트

describe('Monitoring Dashboard', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="dashboard"></div>
            <div id="setting-modal" style="display: none;"></div>
            <div id="detail-modal" style="display: none;"></div>
        `;
    });

    test('프로젝트 카드 렌더링', () => {
        const project = {
            id: 1,
            title: 'Test Project',
            url: 'https://example.com',
            status: 'ok',
            statusText: '정상',
            interval: 60,
            sslStatus: '유효',
            sslExpiry: '2025-12-31',
            domainExpiry: '2025-01-15',
            jsMetrics: 'A+ (98점)'
        };

        const card = renderProjectCard(project);
        expect(card).toContain(project.title);
        expect(card).toContain(project.url);
        expect(card).toContain(project.statusText);
    });

    test('모달 열기/닫기', () => {
        openModal();
        expect(document.getElementById('setting-modal').style.display).toBe('flex');

        closeModal();
        expect(document.getElementById('setting-modal').style.display).toBe('none');
    });

    test('알림 표시', () => {
        showNotification('Test notification');
        const notification = document.querySelector('.notification');
        expect(notification).toBeTruthy();
        expect(notification.textContent).toBe('Test notification');
    });

    test('날짜 포맷팅', () => {
        const date = new Date('2024-01-01T12:00:00');
        const formatted = formatDate(date.toISOString());
        expect(formatted).toMatch(/\d{4}년 \d{2}월 \d{2}일 \d{2}:\d{2}/);
    });

    test('알림 타입 레이블 변환', () => {
        expect(getAlertTypeLabel('status_error')).toBe('상태 오류');
        expect(getAlertTypeLabel('ssl_error')).toBe('SSL 오류');
        expect(getAlertTypeLabel('domain_expiry')).toBe('도메인 만료');
        expect(getAlertTypeLabel('monitoring_error')).toBe('모니터링 오류');
        expect(getAlertTypeLabel('unknown_type')).toBe('unknown_type');
    });
});

describe('API Integration', () => {
    beforeEach(() => {
        global.fetch = jest.fn();
    });

    test('프로젝트 목록 조회', async () => {
        const mockProjects = [
            { id: 1, title: 'Project 1' },
            { id: 2, title: 'Project 2' }
        ];

        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: () => Promise.resolve(mockProjects)
        });

        const projects = await getProjects();
        expect(projects).toEqual(mockProjects);
        expect(global.fetch).toHaveBeenCalledWith(
            'http://localhost:8000/api/monitoring/projects',
            expect.any(Object)
        );
    });

    test('모니터링 설정 업데이트', async () => {
        const mockSettings = {
            check_interval: 300,
            timeout: 30,
            retry_count: 3
        };

        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: () => Promise.resolve(mockSettings)
        });

        await updateMonitoringSettings(1, mockSettings);
        expect(global.fetch).toHaveBeenCalledWith(
            'http://localhost:8000/api/monitoring/settings/1',
            expect.objectContaining({
                method: 'PUT',
                body: JSON.stringify(mockSettings)
            })
        );
    });

    test('알림 해결', async () => {
        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: () => Promise.resolve({ id: 1, is_resolved: true })
        });

        await resolveAlert(1);
        expect(global.fetch).toHaveBeenCalledWith(
            'http://localhost:8000/api/monitoring/alerts/1/resolve',
            expect.objectContaining({
                method: 'POST'
            })
        );
    });
});

describe('Error Handling', () => {
    beforeEach(() => {
        global.fetch = jest.fn();
        console.error = jest.fn();
    });

    test('API 요청 실패 처리', async () => {
        global.fetch.mockRejectedValueOnce(new Error('Network error'));

        const projects = await getProjects();
        expect(projects).toEqual([]);
        expect(console.error).toHaveBeenCalled();
    });

    test('인증 실패 처리', async () => {
        global.fetch.mockResolvedValueOnce({
            status: 401,
            ok: false
        });

        const projects = await getProjects();
        expect(projects).toEqual([]);
        expect(window.location.href).toContain('/login.html');
    });
}); 