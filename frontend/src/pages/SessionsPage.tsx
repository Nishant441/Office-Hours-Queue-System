import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { sessionsAPI } from '../api/sessions';
import { ticketsAPI } from '../api/tickets';
import { coursesAPI } from '../api/courses';
import { useWebSocket } from '../hooks/useWebSocket';
import { OfficeHoursSession, Ticket, Course, SessionStats } from '../api/types';
import { LoadingSpinner } from '../components/UI/LoadingSpinner';
import { ErrorMessage } from '../components/UI/ErrorMessage';
import { EmptyState } from '../components/UI/EmptyState';
import clsx from 'clsx';

export const SessionsPage: React.FC = () => {
    const { user } = useAuth();
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const courseId = searchParams.get('course');

    const [course, setCourse] = useState<Course | null>(null);
    const [session, setSession] = useState<OfficeHoursSession | null>(null);
    const [tickets, setTickets] = useState<Ticket[]>([]);
    const [stats, setStats] = useState<SessionStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [showCreateSession, setShowCreateSession] = useState(false);

    // WebSocket for real-time updates
    useWebSocket(session?.id || null, (data) => {
        if (data.type === 'TICKET_UPDATED') {
            console.log('Real-time update received:', data);
            refreshTickets();
        }
    });

    useEffect(() => {
        if (!courseId) {
            navigate('/dashboard');
            return;
        }
        loadSessionData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [courseId]);

    const loadSessionData = async () => {
        if (!courseId) return;
        setLoading(true);
        setError('');

        try {
            // Load course details
            const courses = await coursesAPI.list();
            const foundCourse = courses.find((c) => c.id === courseId);
            if (!foundCourse) {
                setError('Course not found');
                setLoading(false);
                return;
            }
            setCourse(foundCourse);

            // Load active session (if any)
            const active = await sessionsAPI.getActive(courseId);
            if (active) {
                setSession(active);
                await loadSessionDetails(active.id);
            } else {
                setSession(null);
                setTickets([]);
                setStats(null);
            }

            setLoading(false);
        } catch (err: any) {
            setError(err.message || 'Failed to load session data');
            setLoading(false);
        }
    };

    const loadSessionDetails = async (sessionId: string) => {
        try {
            setError('');

            const sessionData = await sessionsAPI.get(sessionId);
            setSession(sessionData);

            // Now allowed for STUDENT too (backend filters to own tickets)
            const ticketsData = await ticketsAPI.listBySession(sessionId);
            setTickets(ticketsData);

            // Only TA/ADMIN can get stats
            if (user?.role === 'TA' || user?.role === 'ADMIN') {
                const statsData = await sessionsAPI.getStats(sessionId);
                setStats(statsData);
            } else {
                setStats(null);
            }
        } catch (err: any) {
            setError(err.message || 'Failed to load session details');
        }
    };

    const handleCreateSession = async (startsAt: string, endsAt: string) => {
        if (!courseId) return;

        try {
            const newSession = await sessionsAPI.create({
                course_id: courseId,
                starts_at: startsAt,
                ends_at: endsAt,
            });
            setSession(newSession);
            await loadSessionDetails(newSession.id);
            setShowCreateSession(false);
        } catch (err: any) {
            setError(err.message || 'Failed to create session');
        }
    };

    const handleCloseSession = async () => {
        if (!session) return;

        try {
            // close returns updated session
            const updated = await sessionsAPI.close(session.id);
            setSession(updated);

            // refresh the UI so the "Active" badge changes immediately
            await loadSessionDetails(updated.id);
        } catch (err: any) {
            setError(err.message || 'Failed to close session');
        }
    };

    const refreshTickets = async () => {
        if (!session) return;
        await loadSessionDetails(session.id);
    };

    if (loading) return <LoadingSpinner message="Loading session..." />;
    if (!course) return <ErrorMessage message="Course not found" />;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">{course.code}</h1>
                    <p className="mt-1 text-sm text-gray-500">{course.name}</p>
                </div>

                {/* Back button (not dashboard hardcode) */}
                <button onClick={() => navigate(-1)} className="btn-secondary">
                    Back
                </button>
            </div>

            {error && <ErrorMessage message={error} onRetry={loadSessionData} />}

            {!session ? (
                <div className="card">
                    <h2 className="text-xl font-semibold mb-4">Office Hours Session</h2>

                    {(user?.role === 'ADMIN' || user?.role === 'TA') && !showCreateSession && (
                        <EmptyState
                            title="No active session"
                            description="Create a new office hours session to get started"
                            action={{
                                label: 'Create Session',
                                onClick: () => setShowCreateSession(true),
                            }}
                        />
                    )}

                    {showCreateSession && (
                        <CreateSessionForm
                            onSubmit={handleCreateSession}
                            onCancel={() => setShowCreateSession(false)}
                        />
                    )}

                    {user?.role === 'STUDENT' && (
                        <EmptyState
                            title="No active session"
                            description="Office hours are not currently available for this course"
                        />
                    )}
                </div>
            ) : (
                <SessionView
                    session={session}
                    tickets={tickets}
                    stats={stats}
                    onRefresh={refreshTickets}
                    onClose={handleCloseSession}
                />
            )}
        </div>
    );
};

// Create Session Form Component
const CreateSessionForm: React.FC<{
    onSubmit: (startsAt: string, endsAt: string) => void;
    onCancel: () => void;
}> = ({ onSubmit, onCancel }) => {
    const [startsAt, setStartsAt] = useState('');
    const [endsAt, setEndsAt] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(startsAt, endsAt);
    };

    useEffect(() => {
        const now = new Date();
        const twoHoursLater = new Date(now.getTime() + 2 * 60 * 60 * 1000);
        setStartsAt(now.toISOString().slice(0, 16));
        setEndsAt(twoHoursLater.toISOString().slice(0, 16));
    }, []);

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700">Starts At</label>
                    <input
                        type="datetime-local"
                        value={startsAt}
                        onChange={(e) => setStartsAt(e.target.value)}
                        className="input-field"
                        required
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700">Ends At</label>
                    <input
                        type="datetime-local"
                        value={endsAt}
                        onChange={(e) => setEndsAt(e.target.value)}
                        className="input-field"
                        required
                    />
                </div>
            </div>
            <div className="flex space-x-2">
                <button type="submit" className="btn-primary">
                    Create Session
                </button>
                <button type="button" onClick={onCancel} className="btn-secondary">
                    Cancel
                </button>
            </div>
        </form>
    );
};

// Session View Component
const SessionView: React.FC<{
    session: OfficeHoursSession;
    tickets: Ticket[];
    stats: SessionStats | null;
    onRefresh: () => void;
    onClose: () => void;
}> = ({ session, tickets, stats, onRefresh, onClose }) => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [showCreateTicket, setShowCreateTicket] = useState(false);

    const formatTime = (dateString: string) => new Date(dateString).toLocaleString();

    return (
        <>
            <div className="card">
                <div className="flex justify-between items-start">
                    <div>
                        <h2 className="text-xl font-semibold">Office Hours Session</h2>
                        <p className="text-sm text-gray-500 mt-1">
                            {formatTime(session.starts_at)} - {formatTime(session.ends_at)}
                        </p>
                        <div className="mt-2">
                            <span className={clsx('badge', session.is_active ? 'badge-open' : 'badge-cancelled')}>
                                {session.is_active ? 'Active' : 'Closed'}
                            </span>
                        </div>
                    </div>

                    <div className="flex space-x-2">
                        {session.is_active && (
                            <>
                                {user?.role === 'STUDENT' && (
                                    <button
                                        onClick={() => setShowCreateTicket(!showCreateTicket)}
                                        className="btn-primary"
                                    >
                                        {showCreateTicket ? 'Cancel' : 'Create Ticket'}
                                    </button>
                                )}

                                {(user?.role === 'ADMIN' || user?.role === 'TA') && (
                                    <button onClick={onClose} className="btn-danger">
                                        Close Session
                                    </button>
                                )}
                            </>
                        )}

                        <button onClick={onRefresh} className="btn-secondary">
                            Refresh
                        </button>
                    </div>
                </div>

                {/* Only show stats if provided (TA/ADMIN) */}
                {stats && (
                    <div className="mt-6 grid grid-cols-3 gap-4">
                        <div className="bg-blue-50 p-4 rounded-lg">
                            <p className="text-sm text-gray-600">Open</p>
                            <p className="text-2xl font-bold text-blue-600">{stats.count_open}</p>
                        </div>
                        <div className="bg-yellow-50 p-4 rounded-lg">
                            <p className="text-sm text-gray-600">In Progress</p>
                            <p className="text-2xl font-bold text-yellow-600">
                                {stats.count_claimed + stats.count_in_progress}
                            </p>
                        </div>
                        <div className="bg-green-50 p-4 rounded-lg">
                            <p className="text-sm text-gray-600">Resolved</p>
                            <p className="text-2xl font-bold text-green-600">{stats.count_resolved}</p>
                        </div>
                    </div>
                )}
            </div>

            {showCreateTicket && (
                <div className="card">
                    <h3 className="text-lg font-semibold mb-4">Create New Ticket</h3>
                    <CreateTicketButton
                        sessionId={session.id}
                        onSuccess={() => {
                            setShowCreateTicket(false);
                            onRefresh();
                        }}
                    />
                </div>
            )}

            <div className="card">
                <h3 className="text-lg font-semibold mb-4">
                    {user?.role === 'STUDENT' ? 'Your Tickets' : 'Tickets Queue'}
                </h3>

                {tickets.length === 0 ? (
                    <EmptyState
                        title="No tickets"
                        description={session.is_active ? 'No tickets yet' : 'Session is closed'}
                    />
                ) : (
                    <div className="space-y-3">
                        {tickets.map((ticket) => (
                            <TicketCard
                                key={ticket.id}
                                ticket={ticket}
                                onClick={() => navigate(`/tickets/${ticket.id}`)}
                                onRefresh={onRefresh}
                            />
                        ))}
                    </div>
                )}
            </div>
        </>
    );
};

const TicketCard: React.FC<{
    ticket: Ticket;
    onClick: () => void;
    onRefresh: () => void;
}> = ({ ticket, onClick, onRefresh }) => {
    const { user } = useAuth();
    const [actioning, setActioning] = useState(false);

    const handleClaim = async (e: React.MouseEvent) => {
        e.stopPropagation();
        setActioning(true);
        try {
            await ticketsAPI.claim(ticket.id);
            onRefresh();
        } finally {
            setActioning(false);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'OPEN':
                return 'badge-open';
            case 'CLAIMED':
                return 'badge-claimed';
            case 'IN_PROGRESS':
                return 'badge-in-progress';
            case 'RESOLVED':
                return 'badge-resolved';
            case 'CANCELLED':
                return 'badge-cancelled';
            default:
                return 'badge-open';
        }
    };

    // Only TA can claim
    const canClaim = user?.role === 'TA' && ticket.status === 'OPEN';

    return (
        <div onClick={onClick} className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer bg-white">
            <div className="flex justify-between items-start">
                <div className="flex-1">
                    <h4 className="font-semibold">{ticket.title}</h4>
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">{ticket.description}</p>
                    {ticket.topic_tag && (
                        <span className="inline-block mt-2 px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                            {ticket.topic_tag}
                        </span>
                    )}
                </div>

                <div className="ml-4 flex flex-col items-end space-y-2">
                    <span className={clsx('badge', getStatusColor(ticket.status))}>{ticket.status}</span>

                    {canClaim && (
                        <button onClick={handleClaim} className="btn-primary text-xs" disabled={actioning}>
                            {actioning ? 'Claiming...' : 'Claim'}
                        </button>
                    )}
                </div>
            </div>

            <p className="text-xs text-gray-500 mt-2">Created {new Date(ticket.created_at).toLocaleString()}</p>
        </div>
    );
};

const CreateTicketButton: React.FC<{ sessionId: string; onSuccess: () => void }> = ({ sessionId }) => {
    const navigate = useNavigate();

    return (
        <button onClick={() => navigate(`/tickets/create?session=${sessionId}`)} className="btn-primary w-full">
            Create Ticket with Duplicate Detection
        </button>
    );
};
