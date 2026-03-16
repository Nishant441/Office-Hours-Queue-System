import apiClient from "./client";
import { Ticket, TicketCreate, TicketCreateResponse } from "./types";

export const ticketsAPI = {
    async listBySession(sessionId: string): Promise<Ticket[]> {
        // NOTE: must match backend route: /tickets/sessions/{session_id}/tickets
        const res = await apiClient.get(`/api/v1/tickets/sessions/${sessionId}/tickets`);
        return res.data;
    },

    async get(ticketId: string): Promise<Ticket> {
        const res = await apiClient.get(`/api/v1/tickets/${ticketId}`);
        return res.data;
    },

    async create(payload: TicketCreate): Promise<TicketCreateResponse> {
        const res = await apiClient.post(`/api/v1/tickets`, payload);
        return res.data;
    },

    async claim(ticketId: string): Promise<Ticket> {
        const res = await apiClient.post(`/api/v1/tickets/${ticketId}/claim`);
        return res.data;
    },

    async start(ticketId: string): Promise<Ticket> {
        const res = await apiClient.post(`/api/v1/tickets/${ticketId}/start`);
        return res.data;
    },

    async resolve(ticketId: string): Promise<Ticket> {
        const res = await apiClient.post(`/api/v1/tickets/${ticketId}/resolve`);
        return res.data;
    },

    async cancel(ticketId: string): Promise<Ticket> {
        const res = await apiClient.post(`/api/v1/tickets/${ticketId}/cancel`);
        return res.data;
    },
};
