import apiClient from "./client";
import { User } from "./types";

export const usersAPI = {
    async list(role?: "STUDENT" | "TA" | "ADMIN"): Promise<User[]> {
        const params = role ? { role } : {};
        const res = await apiClient.get<User[]>("/api/v1/users/", { params });
        return res.data;
    },
};
