import apiClient from './client';
import { OfficeHoursSession, SessionCreate, SessionStats } from './types';

export const sessionsAPI = {
    async create(data: SessionCreate): Promise<OfficeHoursSession> {
        const response = await apiClient.post<OfficeHoursSession>('/api/v1/sessions/', data);
        return response.data;
    },

    async get(sessionId: string): Promise<OfficeHoursSession> {
        const response = await apiClient.get<OfficeHoursSession>(`/api/v1/sessions/${sessionId}`);
        return response.data;
    },

    async close(sessionId: string): Promise<OfficeHoursSession> {
        const response = await apiClient.post<OfficeHoursSession>(`/api/v1/sessions/${sessionId}/close`);
        return response.data;
    },

    async getStats(sessionId: string): Promise<SessionStats> {
        const response = await apiClient.get<SessionStats>(`/api/v1/sessions/${sessionId}/stats`);
        return response.data;
    },

    // ✅ new
    async getActive(courseId: string): Promise<OfficeHoursSession | null> {
        const response = await apiClient.get<OfficeHoursSession | null>(`/api/v1/sessions/active`, {
            params: { course_id: courseId },
        });
        return response.data;
    },
};
