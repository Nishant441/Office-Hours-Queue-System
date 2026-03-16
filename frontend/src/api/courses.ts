import apiClient from './client';
import { Course, CourseCreate } from './types';

export const coursesAPI = {
    async list(): Promise<Course[]> {
        const response = await apiClient.get<Course[]>('/api/v1/courses/');
        return response.data;
    },

    async create(data: CourseCreate): Promise<Course> {
        const response = await apiClient.post<Course>('/api/v1/courses/', data);
        return response.data;
    },

    async assignStaff(courseId: string, userId: string): Promise<{ message: string }> {
        const response = await apiClient.post<{ message: string }>(
            `/api/v1/courses/${courseId}/staff/${userId}`
        );
        return response.data;
    },

    async removeStaff(courseId: string, userId: string): Promise<void> {
        await apiClient.delete(`/api/v1/courses/${courseId}/staff/${userId}`);
    },

    async delete(id: string): Promise<void> {
        await apiClient.delete(`/api/v1/courses/${id}`);
    },
};
