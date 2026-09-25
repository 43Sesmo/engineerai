"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient, Conversation, Project } from "../lib/api-client";

interface ConversationListProps {
  projectId: number;
}

export default function ConversationList({ projectId }: ConversationListProps) {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(null);

    async function load() {
      try {
        // Relocated from ChatWindow (Sprint 4 §7.1, approved): same
        // client-side workaround for the missing GET /api/projects/{id}
        // — reuse listProjects() and find the match by id. The
        // underlying gap stays out of scope for this sprint; only its
        // usage location moved.
        const projects = await apiClient.listProjects();
        if (!cancelled) {
          const found = projects.find((p) => p.id === projectId) ?? null;
          setProject(found);
        }

        const loadedConversations = await apiClient.listConversations(
          projectId
        );
        if (!cancelled) {
          setConversations(loadedConversations);
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(
            err instanceof Error ? err.message : "Failed to load conversations."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  async function handleNewConversation() {
    setCreating(true);
    setCreateError(null);
    try {
      const conversation = await apiClient.createConversation(projectId, {});
      router.push(`/projects/${projectId}/chat/${conversation.id}`);
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "Failed to start a new conversation."
      );
      setCreating(false);
    }
  }

  if (loadError) {
    return <p className="text-red-600">Error: {loadError}</p>;
  }

  return (
    <div className="w-full max-w-2xl mx-auto flex flex-col gap-4">
      <h1 className="text-2xl font-bold">
        {project ? project.title : `Project #${projectId}`}
      </h1>

      {loading ? (
        <p>Loading conversations...</p>
      ) : (
        <div className="flex flex-col gap-2 border rounded p-4 min-h-[200px]">
          {conversations.length === 0 ? (
            <p className="text-gray-500">No conversations yet.</p>
          ) : (
            conversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() =>
                  router.push(
                    `/projects/${projectId}/chat/${conversation.id}`
                  )
                }
                className="text-left border rounded px-3 py-2 hover:bg-gray-50"
              >
                <div className="font-semibold">
                  {conversation.title ?? `Conversation #${conversation.id}`}
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(conversation.created_at).toLocaleString()}
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {createError && <p className="text-red-600">{createError}</p>}

      <button
        onClick={handleNewConversation}
        disabled={creating}
        className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50 self-start"
      >
        {creating ? "Starting..." : "New Conversation"}
      </button>
    </div>
  );
}
