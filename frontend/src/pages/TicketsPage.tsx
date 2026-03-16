import React, { useState, useEffect } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { ticketsAPI } from "../api/tickets";
import { Ticket, TicketCreateResponse, DuplicateTicket } from "../api/types";
import { LoadingSpinner } from "../components/UI/LoadingSpinner";
import { ErrorMessage } from "../components/UI/ErrorMessage";
import { useAuth } from "../contexts/AuthContext";
import clsx from "clsx";

export const TicketsPage: React.FC = () => {
    const { ticketId } = useParams<{ ticketId: string }>();
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const sessionId = searchParams.get("session");

    // Determine if we're creating a ticket or viewing one
    const isCreateMode = ticketId === "create" && sessionId;

    if (isCreateMode) {
        return <CreateTicketPage sessionId={sessionId as string} />;
    }

    if (ticketId) {
        return <ViewTicketPage ticketId={ticketId} />;
    }

    navigate("/dashboard");
    return null;
};

// Create Ticket Page with Duplicate Detection
const CreateTicketPage: React.FC<{ sessionId: string }> = ({ sessionId }) => {
    const navigate = useNavigate();
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [topicTag, setTopicTag] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [duplicates, setDuplicates] = useState<DuplicateTicket[]>([]);
    const [showDuplicates, setShowDuplicates] = useState(false);
    const [createdTicket, setCreatedTicket] = useState<Ticket | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        setError("");

        try {
            const response: TicketCreateResponse = await ticketsAPI.create({
                session_id: sessionId,
                title,
                description,
                topic_tag: topicTag || undefined,
            });

            setCreatedTicket(response.ticket);
            setDuplicates(response.possible_duplicates);

            if (response.possible_duplicates.length > 0) {
                setShowDuplicates(true);
            }
        } catch (err: any) {
            setError(err.message || "Failed to create ticket");
        } finally {
            setSubmitting(false);
        }
    };

    const handleContinue = () => {
        if (createdTicket) {
            navigate(`/tickets/${createdTicket.id}`);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold text-gray-900">Create Support Ticket</h1>
                <button onClick={() => navigate(-1)} className="btn-secondary">
                    Cancel
                </button>
            </div>

            {error && <ErrorMessage message={error} />}

            {!createdTicket ? (
                <div className="card">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                                Title <span className="text-red-500">*</span>
                            </label>
                            <input
                                id="title"
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                className="input-field"
                                placeholder="Brief summary of your issue"
                                required
                                disabled={submitting}
                            />
                        </div>

                        <div>
                            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                                Description <span className="text-red-500">*</span>
                            </label>
                            <textarea
                                id="description"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                className="input-field"
                                rows={6}
                                placeholder="Detailed description of your issue..."
                                required
                                disabled={submitting}
                            />
                        </div>

                        <div>
                            <label htmlFor="topicTag" className="block text-sm font-medium text-gray-700">
                                Topic Tag (optional)
                            </label>
                            <input
                                id="topicTag"
                                type="text"
                                value={topicTag}
                                onChange={(e) => setTopicTag(e.target.value)}
                                className="input-field"
                                placeholder="e.g., Homework 1, Lecture 3"
                                disabled={submitting}
                            />
                        </div>

                        <button type="submit" className="btn-primary w-full" disabled={submitting}>
                            {submitting ? "Creating ticket..." : "Create Ticket"}
                        </button>
                    </form>
                </div>
            ) : (
                <div className="space-y-6">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-start">
                            <div className="flex-shrink-0">
                                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                                    <path
                                        fillRule="evenodd"
                                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                        clipRule="evenodd"
                                    />
                                </svg>
                            </div>
                            <div className="ml-3">
                                <h3 className="text-sm font-medium text-green-800">Ticket created successfully!</h3>
                                <p className="mt-2 text-sm text-green-700">
                                    Ticket ID:{" "}
                                    <code className="font-mono bg-green-100 px-1 rounded">{createdTicket.id.slice(0, 8)}</code>
                                </p>
                            </div>
                        </div>
                    </div>

                    {showDuplicates && duplicates.length > 0 && (
                        <div className="card">
                            <div className="flex items-start space-x-3 mb-4">
                                <div className="flex-shrink-0">
                                    <svg className="h-6 w-6 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                                        />
                                    </svg>
                                </div>
                                <div className="flex-1">
                                    <h3 className="text-lg font-semibold text-gray-900">Potential Duplicate Tickets Detected</h3>
                                    <p className="text-sm text-gray-600 mt-1">
                                        We found {duplicates.length} similar ticket{duplicates.length > 1 ? "s" : ""}.
                                    </p>
                                </div>
                            </div>

                            <div className="space-y-3 mt-4">
                                {duplicates.map((dup, index) => (
                                    <DuplicateTicketCard key={dup.ticket_id} duplicate={dup} rank={index + 1} />
                                ))}
                            </div>
                        </div>
                    )}

                    {duplicates.length === 0 && (
                        <div className="card bg-blue-50 border-blue-200">
                            <div className="flex items-center space-x-3">
                                <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <div>
                                    <h3 className="text-sm font-medium text-blue-900">No Duplicates Found</h3>
                                    <p className="text-sm text-blue-700 mt-1">Your ticket appears to be unique.</p>
                                </div>
                            </div>
                        </div>
                    )}

                    <button onClick={handleContinue} className="btn-primary w-full">
                        View My Ticket
                    </button>
                </div>
            )}
        </div>
    );
};

const DuplicateTicketCard: React.FC<{ duplicate: DuplicateTicket; rank: number }> = ({ duplicate, rank }) => {
    const percentage = Math.round(duplicate.similarity * 100);

    const getSimilarityColor = (similarity: number) => {
        if (similarity >= 0.8) return "red";
        if (similarity >= 0.6) return "amber";
        return "yellow";
    };

    const color = getSimilarityColor(duplicate.similarity);

    return (
        <div
            className={clsx(
                "border-2 rounded-lg p-4 transition-all",
                color === "red" && "border-red-200 bg-red-50",
                color === "amber" && "border-amber-200 bg-amber-50",
                color === "yellow" && "border-yellow-200 bg-yellow-50"
            )}
        >
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <div className="flex items-center space-x-2">
                        <span
                            className={clsx(
                                "inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold",
                                color === "red" && "bg-red-200 text-red-800",
                                color === "amber" && "bg-amber-200 text-amber-800",
                                color === "yellow" && "bg-yellow-200 text-yellow-800"
                            )}
                        >
                            #{rank}
                        </span>
                        <h4 className="font-semibold text-gray-900">{duplicate.title}</h4>
                    </div>

                    <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                        <span className={clsx("badge", `badge-${String(duplicate.status).toLowerCase()}`)}>
                            {duplicate.status}
                        </span>
                        <span>Created {new Date(duplicate.created_at).toLocaleDateString()}</span>
                    </div>
                </div>

                <div className="ml-4 flex flex-col items-end">
                    <div className="text-right mb-2">
                        <div
                            className={clsx(
                                "text-2xl font-bold",
                                color === "red" && "text-red-600",
                                color === "amber" && "text-amber-600",
                                color === "yellow" && "text-yellow-600"
                            )}
                        >
                            {percentage}%
                        </div>
                        <div className="text-xs text-gray-500">similar</div>
                    </div>

                    <div className="w-24 bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div
                            className={clsx(
                                "h-full rounded-full transition-all",
                                color === "red" && "bg-red-500",
                                color === "amber" && "bg-amber-500",
                                color === "yellow" && "bg-yellow-500"
                            )}
                            style={{ width: `${percentage}%` }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

const ViewTicketPage: React.FC<{ ticketId: string }> = ({ ticketId }) => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [ticket, setTicket] = useState<Ticket | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [actioning, setActioning] = useState(false);

    useEffect(() => {
        loadTicket();
    }, [ticketId]);

    const loadTicket = async () => {
        setLoading(true);
        setError("");

        try {
            const ticketData = await ticketsAPI.get(ticketId);
            setTicket(ticketData);
        } catch (err: any) {
            setError(err.message || "Failed to load ticket");
        } finally {
            setLoading(false);
        }
    };

    const handleStateTransition = async (action: "claim" | "start" | "resolve" | "cancel") => {
        if (!ticket) return;

        setActioning(true);
        try {
            let updatedTicket: Ticket;

            switch (action) {
                case "claim":
                    updatedTicket = await ticketsAPI.claim(ticketId);
                    break;
                case "start":
                    updatedTicket = await ticketsAPI.start(ticketId);
                    break;
                case "resolve":
                    updatedTicket = await ticketsAPI.resolve(ticketId);
                    break;
                case "cancel":
                    updatedTicket = await ticketsAPI.cancel(ticketId);
                    break;
            }

            setTicket(updatedTicket);
        } catch (err: any) {
            setError(err.message || `Failed to ${action} ticket`);
        } finally {
            setActioning(false);
        }
    };

    if (loading) return <LoadingSpinner message="Loading ticket..." />;
    if (!ticket) return <ErrorMessage message={error || "Ticket not found"} />;

    const isOwner = user?.id === ticket.student_id;
    const isAssigned = user?.id === ticket.assigned_ta_id;
    const isTA = user?.role === "TA";

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold text-gray-900">Ticket Details</h1>
                <button onClick={() => navigate(-1)} className="btn-secondary">
                    Back
                </button>
            </div>

            {error && <ErrorMessage message={error} />}

            <div className="card">
                <div className="border-b pb-4 mb-4">
                    <div className="flex justify-between items-start">
                        <div className="flex-1">
                            <h2 className="text-2xl font-bold">{ticket.title}</h2>
                            <p className="text-sm text-gray-500 mt-1">
                                ID:{" "}
                                <code className="font-mono bg-gray-100 px-2 py-1 rounded">{ticket.id.slice(0, 8)}</code>
                            </p>
                        </div>
                        <span className={clsx("badge text-sm", `badge-${ticket.status.toLowerCase().replace("_", "-")}`)}>
                            {ticket.status}
                        </span>
                    </div>
                </div>

                <div className="space-y-4">
                    <div>
                        <h3 className="text-sm font-medium text-gray-700">Description</h3>
                        <p className="mt-2 text-gray-900 whitespace-pre-wrap">{ticket.description}</p>
                    </div>

                    {ticket.topic_tag && (
                        <div>
                            <h3 className="text-sm font-medium text-gray-700">Topic</h3>
                            <span className="inline-block mt-1 px-3 py-1 bg-primary-100 text-primary-800 text-sm rounded-full">
                                {ticket.topic_tag}
                            </span>
                        </div>
                    )}

                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span className="text-gray-600">Created:</span>
                            <span className="ml-2 font-medium">{new Date(ticket.created_at).toLocaleString()}</span>
                        </div>
                        {ticket.claimed_at && (
                            <div>
                                <span className="text-gray-600">Claimed:</span>
                                <span className="ml-2 font-medium">{new Date(ticket.claimed_at).toLocaleString()}</span>
                            </div>
                        )}
                        {ticket.started_at && (
                            <div>
                                <span className="text-gray-600">Started:</span>
                                <span className="ml-2 font-medium">{new Date(ticket.started_at).toLocaleString()}</span>
                            </div>
                        )}
                        {ticket.resolved_at && (
                            <div>
                                <span className="text-gray-600">Resolved:</span>
                                <span className="ml-2 font-medium">{new Date(ticket.resolved_at).toLocaleString()}</span>
                            </div>
                        )}
                    </div>
                </div>

                <div className="mt-6 pt-4 border-t flex space-x-3">
                    {isTA && ticket.status === "OPEN" && (
                        <button onClick={() => handleStateTransition("claim")} className="btn-primary" disabled={actioning}>
                            Claim Ticket
                        </button>
                    )}

                    {isAssigned && ticket.status === "CLAIMED" && (
                        <button onClick={() => handleStateTransition("start")} className="btn-primary" disabled={actioning}>
                            Start Working
                        </button>
                    )}

                    {isAssigned && ticket.status === "IN_PROGRESS" && (
                        <button onClick={() => handleStateTransition("resolve")} className="btn-primary" disabled={actioning}>
                            Mark as Resolved
                        </button>
                    )}

                    {isOwner && (ticket.status === "OPEN" || ticket.status === "CLAIMED") && (
                        <button onClick={() => handleStateTransition("cancel")} className="btn-danger" disabled={actioning}>
                            Cancel Ticket
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};
