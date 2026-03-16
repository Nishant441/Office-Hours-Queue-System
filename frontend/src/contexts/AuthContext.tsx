import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { User } from '../api/types';
import { authAPI } from '../api/auth';

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
    isLoading: boolean;

    // Optional helper: lets you update user fields later
    setUserProfile: (partial: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Save full names keyed by email (fallback for older tokens / older backend)
const displayNameKey = (email: string) => `displayName:${email.toLowerCase()}`;

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const savedToken = localStorage.getItem('token');
        const savedUser = localStorage.getItem('user');

        if (savedToken && savedUser) {
            try {
                setToken(savedToken);
                setUser(JSON.parse(savedUser));
            } catch (error) {
                console.error('Failed to parse saved user:', error);
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
        }

        setIsLoading(false);
    }, []);

    const login = async (email: string, password: string) => {
        const tokenResponse = await authAPI.login({ email, password });

        const accessToken = tokenResponse.access_token;
        localStorage.setItem('token', accessToken);
        setToken(accessToken);

        try {
            const payload = JSON.parse(atob(accessToken.split('.')[1]));

            // ✅ Prefer name from JWT payload (your backend now sends it)
            const nameFromToken = payload?.name ? String(payload.name).trim() : '';

            // Fallback: name saved locally at registration time (older flow)
            const savedDisplayName = localStorage.getItem(displayNameKey(email))?.trim() || '';

            // Last fallback: email prefix
            const fallbackName = email.split('@')[0];

            const bestName = nameFromToken || savedDisplayName || fallbackName;

            const userInfo: User = {
                id: payload.user_id,
                email: payload.email || email,
                name: bestName,
                role: payload.role,
                created_at: new Date().toISOString(),
            };

            localStorage.setItem('user', JSON.stringify(userInfo));
            setUser(userInfo);
        } catch (error) {
            console.error('Failed to decode token:', error);
            throw new Error('Failed to process login token');
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setToken(null);
        setUser(null);
    };

    const setUserProfile = (partial: Partial<User>) => {
        setUser((prev) => {
            if (!prev) return prev;
            const next = { ...prev, ...partial };
            localStorage.setItem('user', JSON.stringify(next));
            return next;
        });
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                login,
                logout,
                isAuthenticated: !!token,
                isLoading,
                setUserProfile,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

// Export this so RegisterPage can save the name after registration (nice fallback)
export const saveDisplayNameForEmail = (email: string, name: string) => {
    if (!email) return;
    const cleaned = (name || '').trim();
    if (!cleaned) return;
    localStorage.setItem(displayNameKey(email), cleaned);
};
