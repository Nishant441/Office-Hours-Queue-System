import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { Layout } from './components/Layout/Layout';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { SessionsPage } from './pages/SessionsPage';
import { TicketsPage } from './pages/TicketsPage';

const DemoPage: React.FC = () => {
    return (
        <div className="card">
            <h2 className="text-xl font-semibold mb-2">Demo Steps</h2>
            <ol className="list-decimal ml-5 space-y-1 text-gray-700">
                <li>Admin: Create a course</li>
                <li>Admin/TA: Create a session for that course</li>
                <li>Student: Join course → create ticket</li>
                <li>TA: Claim → start → resolve ticket</li>
            </ol>
        </div>
    );
};

function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />

                    <Route
                        path="/dashboard"
                        element={
                            <ProtectedRoute>
                                <Layout>
                                    <DashboardPage />
                                </Layout>
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/sessions"
                        element={
                            <ProtectedRoute>
                                <Layout>
                                    <SessionsPage />
                                </Layout>
                            </ProtectedRoute>
                        }
                    />

                    {/* keep your ticket details route */}
                    <Route
                        path="/tickets/:ticketId"
                        element={
                            <ProtectedRoute>
                                <Layout>
                                    <TicketsPage />
                                </Layout>
                            </ProtectedRoute>
                        }
                    />

                    {/* demo route so navbar works */}
                    <Route
                        path="/demo"
                        element={
                            <ProtectedRoute>
                                <Layout>
                                    <DemoPage />
                                </Layout>
                            </ProtectedRoute>
                        }
                    />

                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}

export default App;
