import axios, { AxiosInstance, InternalAxiosRequestConfig } from "axios";

// Use ONE hostname everywhere
const API_BASE_URL = "http://localhost:8000";

export const api: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000,
    headers: {
        "Content-Type": "application/json",
    },
});

// Request interceptor to add auth token
api.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem("token");
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Axios timeout
        if (error.code === "ECONNABORTED") {
            return Promise.reject(
                new Error(
                    `Request timed out (backend not responding). Make sure backend is running on ${API_BASE_URL}`
                )
            );
        }

        if (error.response) {
            if (error.response.status === 401) {
                localStorage.removeItem("token");
                localStorage.removeItem("user");
                window.location.href = "/login";
            }

            const message = extractErrorMessage(error.response.data);
            return Promise.reject(new Error(message));
        }

        // CORS blocked / backend unreachable / DNS / etc.
        return Promise.reject(
            new Error("Network error (no response). Backend unreachable, crashed, or CORS blocked.")
        );
    }
);

function extractErrorMessage(data: any): string {
    if (typeof data === "string") return data;

    if (data?.detail) {
        if (Array.isArray(data.detail)) {
            return data.detail.map((err: any) => err.msg).join(", ");
        }
        return data.detail;
    }

    return "An error occurred";
}

export default api;
