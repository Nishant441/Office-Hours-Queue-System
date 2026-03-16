import apiClient from './client';
import { RegisterRequest, LoginRequest, TokenResponse, User } from './types';

export const authAPI = {
    async register(data: RegisterRequest): Promise<User> {
        const response = await apiClient.post<User>('/api/v1/auth/register', data);
        return response.data;
    },

    async login(data: LoginRequest): Promise<TokenResponse> {
        const response = await apiClient.post<TokenResponse>('/api/v1/auth/login', data);
        return response.data;
    },
};
