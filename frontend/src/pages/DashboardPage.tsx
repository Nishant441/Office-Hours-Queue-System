import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { coursesAPI } from "../api/courses";
import { usersAPI } from "../api/users";
import { Course, User } from "../api/types";
import { LoadingSpinner } from "../components/UI/LoadingSpinner";
import { ErrorMessage } from "../components/UI/ErrorMessage";
import { EmptyState } from "../components/UI/EmptyState";

export const DashboardPage: React.FC = () => {
    const { user } = useAuth();
    const [courses, setCourses] = useState<Course[]>([]);
    const [tas, setTAs] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        setLoading(true);
        setError("");

        try {
            const coursesData = await coursesAPI.list();
            setCourses(coursesData);

            if (user?.role === "ADMIN") {
                const taUsers = await usersAPI.list("TA");
                setTAs(taUsers);
            } else {
                setTAs([]);
            }
        } catch (err: any) {
            setError(err.message || "Failed to load dashboard data");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <LoadingSpinner message="Loading dashboard..." />;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Welcome, {user?.name}</h1>
                    <p className="mt-1 text-sm text-gray-500">
                        Role: <span className="font-medium">{user?.role}</span>
                    </p>
                </div>
            </div>

            {error && <ErrorMessage message={error} onRetry={loadDashboardData} />}

            {user?.role === "ADMIN" && (
                <AdminDashboard courses={courses} tas={tas} onRefresh={loadDashboardData} />
            )}

            {user?.role === "TA" && <TADashboard courses={courses} />}

            {user?.role === "STUDENT" && <StudentDashboard courses={courses} />}
        </div>
    );
};

const AdminDashboard: React.FC<{
    courses: Course[];
    tas: User[];
    onRefresh: () => void;
}> = ({ courses, tas, onRefresh }) => {
    const navigate = useNavigate();

    const [showCreateCourse, setShowCreateCourse] = useState(false);
    const [newCourseCode, setNewCourseCode] = useState("");
    const [newCourseName, setNewCourseName] = useState("");
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState("");

    const [selectedTAByCourse, setSelectedTAByCourse] = useState<Record<string, string>>({});
    const [assigningCourseId, setAssigningCourseId] = useState<string | null>(null);
    const [assignError, setAssignError] = useState("");

    const taOptions = useMemo(() => tas ?? [], [tas]);

    const handleCreateCourse = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreating(true);
        setError("");

        try {
            await coursesAPI.create({ code: newCourseCode, name: newCourseName });
            setNewCourseCode("");
            setNewCourseName("");
            setShowCreateCourse(false);
            onRefresh();
        } catch (err: any) {
            setError(err.message || "Failed to create course");
        } finally {
            setCreating(false);
        }
    };

    const handleAssignTA = async (courseId: string) => {
        setAssignError("");
        const userId = selectedTAByCourse[courseId];

        if (!userId) {
            setAssignError("Pick a TA before assigning.");
            return;
        }

        setAssigningCourseId(courseId);
        try {
            await coursesAPI.assignStaff(courseId, userId);
            setSelectedTAByCourse((prev) => ({ ...prev, [courseId]: "" }));
            onRefresh();
        } catch (err: any) {
            setAssignError(err.message || "Failed to assign TA");
        } finally {
            setAssigningCourseId(null);
        }
    };

    const handleRemoveStaff = async (courseId: string, userId: string) => {
        if (!confirm("Are you sure you want to remove this TA?")) return;

        try {
            await coursesAPI.removeStaff(courseId, userId);
            onRefresh();
        } catch (err: any) {
            setAssignError(err.message || "Failed to remove TA");
        }
    };

    const handleDeleteCourse = async (courseId: string) => {
        if (!confirm("Are you sure? This will delete the course and ALL lists/tickets.")) return;

        try {
            await coursesAPI.delete(courseId);
            onRefresh();
        } catch (err: any) {
            setError(err.message || "Failed to delete course");
        }
    };

    return (
        <div className="space-y-6">
            <div className="card">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-semibold">Courses</h2>
                    <button
                        onClick={() => setShowCreateCourse(!showCreateCourse)}
                        className="btn-primary text-sm"
                    >
                        {showCreateCourse ? "Cancel" : "+ Create Course"}
                    </button>
                </div>

                {showCreateCourse && (
                    <form
                        onSubmit={handleCreateCourse}
                        className="mb-6 p-4 bg-gray-50 rounded-lg space-y-4"
                    >
                        {error && <ErrorMessage message={error} />}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Course Code</label>
                                <input
                                    type="text"
                                    value={newCourseCode}
                                    onChange={(e) => setNewCourseCode(e.target.value)}
                                    className="input-field"
                                    placeholder="CS-101"
                                    required
                                    disabled={creating}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Course Name</label>
                                <input
                                    type="text"
                                    value={newCourseName}
                                    onChange={(e) => setNewCourseName(e.target.value)}
                                    className="input-field"
                                    placeholder="Intro to CS"
                                    required
                                    disabled={creating}
                                />
                            </div>
                        </div>

                        <button type="submit" className="btn-primary" disabled={creating}>
                            {creating ? "Creating..." : "Create Course"}
                        </button>
                    </form>
                )}

                {assignError && <ErrorMessage message={assignError} />}

                {courses.length === 0 ? (
                    <EmptyState
                        title="No courses yet"
                        description="Create your first course to get started"
                        action={{ label: "Create Course", onClick: () => setShowCreateCourse(true) }}
                    />
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {courses.map((course) => (
                            <div key={course.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow relative group">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h3 className="font-semibold text-lg">{course.code}</h3>
                                        <p className="text-gray-600 text-sm">{course.name}</p>
                                    </div>
                                    <button
                                        onClick={() => handleDeleteCourse(course.id)}
                                        className="text-gray-300 hover:text-red-500 transition-colors p-1"
                                        title="Delete Course"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                                        </svg>
                                    </button>
                                </div>

                                <div className="mt-4 flex flex-wrap gap-2">
                                    <button
                                        onClick={() => navigate(`/sessions?course=${course.id}`)}
                                        className="btn-primary text-sm"
                                    >
                                        View Sessions
                                    </button>
                                </div>

                                <div className="mt-4 border-t pt-4">
                                    <p className="text-sm font-medium text-gray-700 mb-2">Staff</p>

                                    {course.staff && course.staff.length > 0 && (
                                        <div className="mb-3 space-y-1">
                                            {course.staff.map(ta => (
                                                <div key={ta.id} className="flex justify-between items-center text-sm bg-gray-50 p-2 rounded">
                                                    <span>{ta.name}</span>
                                                    <button
                                                        onClick={() => handleRemoveStaff(course.id, ta.id)}
                                                        className="text-red-600 hover:text-red-800 text-xs font-medium"
                                                    >
                                                        Remove
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    <p className="text-sm font-medium text-gray-700 mb-2">Assign new TA</p>

                                    {taOptions.length === 0 ? (
                                        <p className="text-sm text-gray-500">No TAs found. Create a TA account first.</p>
                                    ) : (
                                        <div className="flex gap-2 items-center">
                                            <select
                                                className="input-field !mt-0"
                                                value={selectedTAByCourse[course.id] || ""}
                                                onChange={(e) =>
                                                    setSelectedTAByCourse((prev) => ({
                                                        ...prev,
                                                        [course.id]: e.target.value,
                                                    }))
                                                }
                                            >
                                                <option value="">Select TA...</option>
                                                {taOptions.map((ta) => (
                                                    <option key={ta.id} value={ta.id}>
                                                        {ta.name}
                                                    </option>
                                                ))}
                                            </select>

                                            <button
                                                className="btn-secondary text-sm"
                                                onClick={() => handleAssignTA(course.id)}
                                                disabled={assigningCourseId === course.id}
                                            >
                                                {assigningCourseId === course.id ? "Assigning..." : "Assign"}
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

const TADashboard: React.FC<{ courses: Course[] }> = ({ courses }) => {
    const navigate = useNavigate();

    return (
        <div className="space-y-6">
            <div className="card">
                <h2 className="text-xl font-semibold mb-4">Your Courses</h2>

                {courses.length === 0 ? (
                    <EmptyState title="No courses assigned" description="Ask an admin to assign you to a course" />
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {courses.map((course) => (
                            <div key={course.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                                <h3 className="font-semibold text-lg">{course.code}</h3>
                                <p className="text-gray-600 text-sm">{course.name}</p>

                                <button
                                    onClick={() => navigate(`/sessions?course=${course.id}`)}
                                    className="mt-4 btn-primary text-sm"
                                >
                                    View Office Hours
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

const StudentDashboard: React.FC<{ courses: Course[] }> = ({ courses }) => {
    const navigate = useNavigate();

    return (
        <div className="space-y-6">
            <div className="card">
                <h2 className="text-xl font-semibold mb-4">Available Courses</h2>

                {courses.length === 0 ? (
                    <EmptyState title="No courses available" description="No courses have been created yet" />
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {courses.map((course) => (
                            <div key={course.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                                <h3 className="font-semibold text-lg">{course.code}</h3>
                                <p className="text-gray-600 text-sm">{course.name}</p>

                                <button
                                    onClick={() => navigate(`/sessions?course=${course.id}`)}
                                    className="mt-4 btn-primary text-sm"
                                >
                                    Join Office Hours
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
