/**
 * EngineerAI frontend — API client.
 *
 * One clean place to call the backend, instead of scattering fetch calls
 * through components. Every exported function routes through a single
 * request<T>() helper, matching one real backend endpoint from Tasks 9-11
 * each — no more, no less.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// --- Types, matching the backend's response schemas field-for-field -----

export interface Project {
  id: number;
  user_id: number;
  title: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateInput {
  title: string;
  description?: string | null;
  status?: string;
}

export interface Conversation {
  id: number;
  project_id: number;
  title: string | null;
  created_at: string;
}

export interface ConversationCreateInput {
  title?: string | null;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: string;
  content_text: string;
  structured_output: Record<string, unknown> | null;
  created_at: string;
}

export interface MessageCreateInput {
  content: string;
}

// --- Shared request helper -------------------------------------------

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const errorBody = await response.json();
      detail = errorBody?.detail ?? detail;
    } catch {
      // Response body wasn't JSON — fall back to statusText.
    }
    throw new Error(`API request failed (${response.status}): ${detail}`);
  }

  return response.json() as Promise<T>;
}

// --- Endpoint functions, one per real backend route (Tasks 9-11) --------

function listProjects(): Promise<Project[]> {
  return request<Project[]>("/api/projects");
}

function createProject(input: ProjectCreateInput): Promise<Project> {
  return request<Project>("/api/projects", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

function createConversation(
  projectId: number,
  input: ConversationCreateInput
): Promise<Conversation> {
  return request<Conversation>(`/api/projects/${projectId}/conversations`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

function getConversation(conversationId: number): Promise<Conversation> {
  return request<Conversation>(`/api/conversations/${conversationId}`);
}

function createMessage(
  conversationId: number,
  input: MessageCreateInput
): Promise<Message[]> {
  return request<Message[]>(`/api/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

function listMessages(conversationId: number): Promise<Message[]> {
  return request<Message[]>(`/api/conversations/${conversationId}/messages`);
}

export const apiClient = {
  listProjects,
  createProject,
  createConversation,
  getConversation,
  createMessage,
  listMessages,
};

// --- Dev-only console access ---------------------------------------------
// Approved design: exposes apiClient on window ONLY when NODE_ENV is
// "development" (never true in a production build), purely so it can be
// called directly from the browser DevTools console for Task 13's
// verification. This block is inert in any production build.
if (typeof window !== "undefined" && process.env.NODE_ENV === "development") {
  (window as unknown as { apiClient: typeof apiClient }).apiClient =
    apiClient;
}
