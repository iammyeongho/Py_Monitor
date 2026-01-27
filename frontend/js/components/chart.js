/**
 * PyMonitor - 차트 모듈
 */

const chartManager = {
    // 차트 인스턴스
    responseTimeChart: null,
    availabilityChart: null,
    currentPeriod: 24, // 기본 24시간

    // 색상 팔레트
    colors: [
        'rgb(59, 130, 246)',
        'rgb(16, 185, 129)',
        'rgb(245, 158, 11)',
        'rgb(239, 68, 68)',
        'rgb(139, 92, 246)',
        'rgb(236, 72, 153)',
    ],

    /**
     * 초기화
     */
    init() {
        this.setupPeriodSelector();
        this.loadData(this.currentPeriod);
    },

    /**
     * 기간 선택기 설정
     */
    setupPeriodSelector() {
        document.querySelectorAll('.chart-period-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                // 활성화 상태 변경
                document.querySelectorAll('.chart-period-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // 차트 데이터 다시 로드
                const hours = parseInt(btn.dataset.hours);
                this.currentPeriod = hours;
                this.loadData(hours);
            });
        });
    },

    /**
     * 차트 데이터 로드
     */
    async loadData(hours = 24) {
        try {
            const response = await fetch(`/api/v1/monitoring/charts/dashboard?hours=${hours}`, {
                headers: auth.getAuthHeaders()
            });

            if (response.ok) {
                const data = await response.json();
                this.updateResponseTimeChart(data.response_time);
                this.updateAvailabilityChart(data.availability);
            }
        } catch (error) {
            console.error('차트 데이터 로드 오류:', error);
        }
    },

    /**
     * 응답 시간 차트 업데이트
     */
    updateResponseTimeChart(data) {
        const ctx = document.getElementById('response-time-chart');
        if (!ctx) return;

        // 기존 차트 제거
        if (this.responseTimeChart) {
            this.responseTimeChart.destroy();
        }

        const datasets = data.map((project, index) => ({
            label: project.project_title,
            data: project.data_points.map(point => ({
                x: new Date(point.timestamp),
                y: point.value
            })),
            borderColor: this.colors[index % this.colors.length],
            backgroundColor: this.colors[index % this.colors.length] + '20',
            tension: 0.3,
            fill: false,
            pointRadius: 2,
            pointHoverRadius: 4,
        }));

        this.responseTimeChart = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index',
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                return `${context.dataset.label}: ${value ? Math.round(value) + 'ms' : 'N/A'}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            displayFormats: {
                                hour: 'HH:mm',
                                day: 'MM/dd HH:mm'
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'ms'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                        }
                    }
                }
            }
        });

        // 범례 업데이트
        this.updateLegend(data);
    },

    /**
     * 차트 범례 업데이트
     */
    updateLegend(data) {
        const legendContainer = document.getElementById('response-time-legend');
        if (!legendContainer) return;

        legendContainer.innerHTML = data.map((project, index) => `
            <div class="chart-legend-item">
                <span class="chart-legend-color" style="background-color: ${this.colors[index % this.colors.length]}"></span>
                <span class="chart-legend-label">${utils.escapeHtml(project.project_title)}</span>
                <span class="chart-legend-value">${project.avg_response_time ? Math.round(project.avg_response_time) + 'ms' : '-'}</span>
            </div>
        `).join('');
    },

    /**
     * 가용성 차트 업데이트
     */
    updateAvailabilityChart(data) {
        const ctx = document.getElementById('availability-chart');
        if (!ctx) return;

        // 기존 차트 제거
        if (this.availabilityChart) {
            this.availabilityChart.destroy();
        }

        const labels = data.map(p => p.project_title);
        const values = data.map(p => p.availability_percentage);
        const backgroundColors = values.map(v => {
            if (v >= 99) return 'rgba(16, 185, 129, 0.8)';
            if (v >= 95) return 'rgba(245, 158, 11, 0.8)';
            return 'rgba(239, 68, 68, 0.8)';
        });

        this.availabilityChart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: '가용성',
                    data: values,
                    backgroundColor: backgroundColors,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `가용성: ${context.parsed.x.toFixed(2)}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: '%'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                        }
                    },
                    y: {
                        grid: {
                            display: false,
                        }
                    }
                }
            }
        });

        // 통계 업데이트
        this.updateAvailabilityStats(data);
    },

    /**
     * 가용성 통계 업데이트
     */
    updateAvailabilityStats(data) {
        const statsContainer = document.getElementById('availability-stats');
        if (!statsContainer) return;

        if (data.length === 0) {
            statsContainer.innerHTML = '<p class="no-data">데이터가 없습니다.</p>';
            return;
        }

        const totalChecks = data.reduce((sum, p) => sum + p.total_checks, 0);
        const availableChecks = data.reduce((sum, p) => sum + p.available_checks, 0);
        const avgAvailability = totalChecks > 0 ? (availableChecks / totalChecks * 100) : 0;

        statsContainer.innerHTML = `
            <div class="availability-stat">
                <span class="stat-label">총 체크</span>
                <span class="stat-value">${totalChecks.toLocaleString()}회</span>
            </div>
            <div class="availability-stat">
                <span class="stat-label">성공</span>
                <span class="stat-value">${availableChecks.toLocaleString()}회</span>
            </div>
            <div class="availability-stat">
                <span class="stat-label">평균 가용성</span>
                <span class="stat-value ${avgAvailability >= 99 ? 'good' : avgAvailability >= 95 ? 'warning' : 'bad'}">${avgAvailability.toFixed(2)}%</span>
            </div>
        `;
    }
};

// 전역으로 노출
window.chartManager = chartManager;
