// 프로젝트 관련 함수들
const project = {
    // 프로젝트 목록 조회
    async getProjects() {
        try {
            const response = await fetch('/api/v1/projects', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });
            
            if (!response.ok) {
                throw new Error('프로젝트 목록 조회에 실패했습니다.');
            }
            
            return await response.json();
        } catch (error) {
            console.error('프로젝트 목록 조회 오류:', error);
            throw error;
        }
    },
    
    // 프로젝트 생성
    async createProject(data) {
        try {
            const response = await fetch('/api/v1/projects', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });
            
            if (!response.ok) {
                throw new Error('프로젝트 생성에 실패했습니다.');
            }
            
            return await response.json();
        } catch (error) {
            console.error('프로젝트 생성 오류:', error);
            throw error;
        }
    },
    
    // 프로젝트 수정
    async updateProject(id, data) {
        try {
            const response = await fetch(`/api/v1/projects/${id}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });
            
            if (!response.ok) {
                throw new Error('프로젝트 수정에 실패했습니다.');
            }
            
            return await response.json();
        } catch (error) {
            console.error('프로젝트 수정 오류:', error);
            throw error;
        }
    },
    
    // 프로젝트 삭제
    async deleteProject(id) {
        try {
            const response = await fetch(`/api/v1/projects/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });
            
            if (!response.ok) {
                throw new Error('프로젝트 삭제에 실패했습니다.');
            }
            
            return true;
        } catch (error) {
            console.error('프로젝트 삭제 오류:', error);
            throw error;
        }
    },
    
    // 프로젝트 상세 정보 조회
    async getProjectDetail(id) {
        try {
            const response = await fetch(`/api/v1/projects/${id}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });
            
            if (!response.ok) {
                throw new Error('프로젝트 상세 정보 조회에 실패했습니다.');
            }
            
            return await response.json();
        } catch (error) {
            console.error('프로젝트 상세 정보 조회 오류:', error);
            throw error;
        }
    }
}; 