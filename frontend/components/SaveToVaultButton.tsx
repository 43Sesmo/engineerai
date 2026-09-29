"use client";

import { useState, FormEvent, ChangeEvent } from "react";
import { apiClient, Message } from "../lib/api-client";

const ENTRY_TYPES = [
  "decision",
  "lesson_learned",
  "design_pattern",
  "research_finding",
  "engineering_knowledge",
  "preference",
];

function excerpt(text: string, maxLength = 60): string {
  const trimmed = text.trim();
  if (trimmed.length <= maxLength) return trimmed;
  return `${trimmed.slice(0, maxLength).trim()}...`;
}

interface SaveToVaultButtonProps {
  message: Message;
  conversationId: number;
  projectId: number | null;
}

export default function SaveToVaultButton({
  message,
  conversationId,
  projectId,
}: SaveToVaultButtonProps) {
  const [expanded, setExpanded] = useState(false);
  const [entryType, setEntryType] = useState("");
  const [title, setTitle] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleExpand() {
    setTitle(excerpt(message.content_text));
    setEntryType("");
    setError(null);
    setExpanded(true);
  }

  function handleCancel() {
    setExpanded(false);
    setError(null);
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    if (!entryType || !title.trim()) return;

    setSaving(true);
    setError(null);
    try {
      await apiClient.createKnowledgeEntry({
        title: title.trim(),
        summary: message.content_text,
        entry_type: entryType,
        project_id: projectId,
        content: message.structured_output,
        source_conversation_id: conversationId,
        source_message_id: message.id,
      });
      setSaved(true);
      setExpanded(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to save to Knowledge Vault."
      );
    } finally {
      setSaving(false);
    }
  }

  if (saved) {
    return <span className="text-xs text-green-600">Saved to Vault ✓</span>;
  }

  if (!expanded) {
    return (
      <button
        type="button"
        onClick={handleExpand}
        className="text-xs text-gray-500 border rounded px-2 py-1 self-start hover:bg-gray-50"
      >
        Save to Vault
      </button>
    );
  }

  return (
    <form
      onSubmit={handleSave}
      className="flex flex-col gap-2 border rounded p-2 mt-1"
    >
      <div className="flex gap-2">
        <select
          value={entryType}
          onChange={(e: ChangeEvent<HTMLSelectElement>) =>
            setEntryType(e.target.value)
          }
          className="border rounded px-2 py-1 text-sm"
          disabled={saving}
        >
          <option value="" disabled>
            Select type...
          </option>
          {ENTRY_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
        <input
          type="text"
          value={title}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)}
          className="border rounded px-2 py-1 text-sm flex-1"
          disabled={saving}
        />
      </div>
      {error && <p className="text-red-600 text-xs">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={saving || !entryType || !title.trim()}
          className="bg-blue-600 text-white text-xs px-3 py-1 rounded disabled:opacity-50"
        >
          {saving ? "Saving..." : "Confirm"}
        </button>
        <button
          type="button"
          onClick={handleCancel}
          disabled={saving}
          className="text-xs text-gray-500 px-3 py-1"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
