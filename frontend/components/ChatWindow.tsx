"use client";

import { useEffect, useState, FormEvent, ChangeEvent } from "react";
import { apiClient, Project, Message } from "../lib/api-client";

interface ChatWindowProps {
  projectId: number;
}

export default function ChatWindow({ projectId }: ChatWindowProps) {
  const [project, setProject] = useState<Project | null>(null);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [setupError, setSetupError] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function setup() {
      try {
        // Client-side workaround for the missing GET /api/projects/{id}
        // (approved): reuse listProjects() and find the match by id.
        // Falls back to a numeric label if not found, rather than
        // treating a miss as fatal.
        const projects = await apiClient.listProjects();
        if (!cancelled) {
          const found = projects.find((p) => p.id === projectId) ?? null;
          setProject(found);
        }

        const conversation = await apiClient.createConversation(projectId, {});
        if (cancelled) return;
        setConversationId(conversation.id);

        const existingMessages = await apiClient.listMessages(conversation.id);
        if (!cancelled) {
          setMessages(existingMessages);
        }
      } catch (err) {
        if (!cancelled) {
          setSetupError(
            err instanceof Error ? err.message : "Failed to start conversation."
          );
        }
      }
    }

    setup();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  async function handleSend(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || conversationId === null) return;

    setSending(true);
    setSendError(null);
    const contentSent = input;

    try {
      const newMessages = await apiClient.createMessage(conversationId, {
        content: contentSent,
      });
      setMessages((prev) => [...prev, ...newMessages]);
      setInput("");
    } catch (err) {
      // Approved design: the user's message was already persisted
      // server-side even though this call threw (Task 11's design) — 
      // re-fetch so the transcript reflects that, instead of showing an
      // error while leaving stale state on screen.
      setSendError(
        err instanceof Error ? err.message : "Failed to send message."
      );
      try {
        const refreshed = await apiClient.listMessages(conversationId);
        setMessages(refreshed);
        setInput("");
      } catch {
        // If even the re-fetch fails, leave the typed input in place so
        // nothing the user typed is lost.
      }
    } finally {
      setSending(false);
    }
  }

  if (setupError) {
    return <p className="text-red-600">Error: {setupError}</p>;
  }

  if (conversationId === null) {
    return <p>Starting conversation...</p>;
  }

  return (
    <div className="w-full max-w-2xl mx-auto flex flex-col gap-4">
      <h1 className="text-2xl font-bold">
        {project ? project.title : `Project #${projectId}`}
      </h1>

      <div className="flex flex-col gap-2 border rounded p-4 min-h-[200px]">
        {messages.length === 0 ? (
          <p className="text-gray-500">No messages yet.</p>
        ) : (
          messages.map((message) => (
            <div key={message.id} className="flex flex-col">
              <span className="text-xs font-semibold text-gray-600">
                {message.role === "user" ? "You" : "Claude"}
              </span>
              <p>{message.content_text}</p>
            </div>
          ))
        )}
      </div>

      {sendError && <p className="text-red-600">{sendError}</p>}

      <form onSubmit={handleSend} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 border rounded px-3 py-2"
          disabled={sending}
        />
        <button
          type="submit"
          disabled={sending}
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          {sending ? "Sending..." : "Send"}
        </button>
      </form>
    </div>
  );
}
