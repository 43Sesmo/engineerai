"use client";

import { useEffect, useState, FormEvent, ChangeEvent } from "react";
import { apiClient, Conversation, Message } from "../lib/api-client";
import EngineeringGuidanceView, { EngineeringGuidance } from "./EngineeringGuidanceView";

interface ChatWindowProps {
  conversationId: number;
}

export default function ChatWindow({ conversationId }: ChatWindowProps) {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [setupError, setSetupError] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setSetupError(null);

    async function setup() {
      try {
        // Sprint 4: ChatWindow no longer creates a conversation — it's
        // keyed on an existing conversationId (from the route) and only
        // loads that conversation's own metadata and message history.
        const loadedConversation = await apiClient.getConversation(
          conversationId
        );
        if (cancelled) return;
        setConversation(loadedConversation);

        const existingMessages = await apiClient.listMessages(conversationId);
        if (!cancelled) {
          setMessages(existingMessages);
        }
      } catch (err) {
        if (!cancelled) {
          setSetupError(
            err instanceof Error ? err.message : "Failed to load conversation."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    setup();
    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  async function handleSend(e: FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;

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

  if (loading) {
    return <p>Loading conversation...</p>;
  }

  return (
    <div className="w-full max-w-2xl mx-auto flex flex-col gap-4">
      <h1 className="text-2xl font-bold">
        {conversation?.title ?? `Conversation #${conversationId}`}
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
              {message.structured_output ? (
                <EngineeringGuidanceView
                  data={message.structured_output as unknown as EngineeringGuidance}
                  rawText={message.content_text}
                />
              ) : (
                <p>{message.content_text}</p>
              )}
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
