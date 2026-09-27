"use client";

import { useEffect, useState, FormEvent, ChangeEvent } from "react";
import Link from "next/link";
import { apiClient, KnowledgeEntry, Project } from "../lib/api-client";

const ENTRY_TYPES = [
  "decision",
  "lesson_learned",
  "design_pattern",
  "research_finding",
  "engineering_knowledge",
  "preference",
];

export default function KnowledgeList() {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filterType, setFilterType] = useState<string>("");

  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [entryType, setEntryType] = useState(ENTRY_TYPES[0]);
  const [projectId, setProjectId] = useState<string>(""); // "" = General
  const [creating, setCreating] = useState(false);

  // Projects are fetched once, independently of the entry_type filter —
  // they're only used for the create form's dropdown and the list's
  // project-name badges, matching ConversationList.tsx's own pattern of
  // each component independently calling listProjects() rather than
  // sharing a cache across components.
  useEffect(() => {
    let cancelled = false;

    async function loadProjects() {
      try {
        const result = await apiClient.listProjects();
        if (!cancelled) {
          setProjects(result);
        }
      } catch {
        // Project lookup only feeds badge labels and the create form's
        // dropdown — a failure here shouldn't block the entries list
        // itself from loading and rendering.
      }
    }

    loadProjects();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    async function loadEntries() {
      try {
        const result = await apiClient.listKnowledgeEntries(
          filterType ? { entry_type: filterType } : undefined
        );
        if (!cancelled) {
          setEntries(result);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load knowledge entries."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadEntries();
    return () => {
      cancelled = true;
    };
  }, [filterType]);

  function projectLabel(entryProjectId: number | null): string {
    if (entryProjectId === null) return "General";
    const match = projects.find((p) => p.id === entryProjectId);
    return match ? match.title : `Project #${entryProjectId}`;
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!title.trim() || !summary.trim()) return;

    setCreating(true);
    setError(null);
    try {
      const entry = await apiClient.createKnowledgeEntry({
        title,
        summary,
        entry_type: entryType,
        project_id: projectId ? Number(projectId) : null,
      });
      setEntries((prev) => [...prev, entry]);
      setTitle("");
      setSummary("");
      setProjectId("");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create knowledge entry."
      );
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="w-full max-w-2xl">
      <form
        onSubmit={handleCreate}
        className="flex flex-col gap-2 mb-6 border rounded p-4"
      >
        <input
          type="text"
          value={title}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)}
          placeholder="Title"
          className="border rounded px-3 py-2"
          disabled={creating}
        />
        <textarea
          value={summary}
          onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
            setSummary(e.target.value)
          }
          placeholder="Summary"
          className="border rounded px-3 py-2"
          disabled={creating}
        />
        <div className="flex gap-2">
          <select
            value={entryType}
            onChange={(e: ChangeEvent<HTMLSelectElement>) =>
              setEntryType(e.target.value)
            }
            className="border rounded px-3 py-2"
            disabled={creating}
          >
            {ENTRY_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
          <select
            value={projectId}
            onChange={(e: ChangeEvent<HTMLSelectElement>) =>
              setProjectId(e.target.value)
            }
            className="border rounded px-3 py-2 flex-1"
            disabled={creating}
          >
            <option value="">General (no project)</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.title}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          disabled={creating}
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50 self-start"
        >
          {creating ? "Saving..." : "Save to Vault"}
        </button>
      </form>

      <div className="mb-4">
        <label className="text-sm text-gray-600 mr-2">Filter by type:</label>
        <select
          value={filterType}
          onChange={(e: ChangeEvent<HTMLSelectElement>) =>
            setFilterType(e.target.value)
          }
          className="border rounded px-2 py-1"
        >
          <option value="">All types</option>
          {ENTRY_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="text-red-600 mb-4">{error}</p>}

      {loading ? (
        <p>Loading knowledge entries...</p>
      ) : entries.length === 0 ? (
        <p>No knowledge entries yet.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {entries.map((entry) => (
            <li key={entry.id} className="border rounded px-3 py-2">
              <Link
                href={`/knowledge/${entry.id}`}
                className="font-semibold text-blue-600 underline"
              >
                {entry.title}
              </Link>
              <span className="text-sm text-gray-500 ml-2">
                ({entry.entry_type})
              </span>
              <span className="text-sm text-gray-500 ml-2">
                — {projectLabel(entry.project_id)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
