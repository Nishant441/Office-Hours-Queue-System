import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";


export const Navbar: React.FC = () => {
    const { user, logout, isAuthenticated } = useAuth();

    return (
        <nav className="bg-white shadow-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex">
                        <Link to="/" className="flex items-center">
                            <span className="text-xl font-bold text-primary-600">
                                Office Hours Queue
                            </span>
                        </Link>

                        {isAuthenticated && (
                            <div className="ml-10 flex items-center space-x-4">
                                <Link
                                    to="/dashboard"
                                    className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                                >
                                    Dashboard
                                </Link>
                                <Link
                                    to="/demo"
                                    className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                                >
                                    Demo Steps
                                </Link>
                            </div>
                        )}
                    </div>

                    <div className="flex items-center">
                        {isAuthenticated ? (
                            <div className="flex items-center space-x-4">
                                <span className="text-sm text-gray-700">
                                    {user?.email} ({user?.role})
                                </span>
                                <button onClick={logout} className="btn-secondary text-sm">
                                    Logout
                                </button>
                            </div>
                        ) : (
                            <div className="flex items-center space-x-4">
                                <Link to="/login" className="btn-secondary text-sm">
                                    Login
                                </Link>
                                <Link to="/register" className="btn-primary text-sm">
                                    Register
                                </Link>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </nav>
    );
};
