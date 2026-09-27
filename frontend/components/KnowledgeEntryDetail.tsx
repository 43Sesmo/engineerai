"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiClient, KnowledgeEntry, Project } from "../lib/api-client";

interface KnowledgeEntryDetailProps {
  entryId: number;
}

export default function KnowledgeEntryDetail({
  entryId,
}: KnowledgeEntryDetailProps) {
  const [entry, setEntry] = useState<KnowledgeEntry | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    async function load() {
      try {
        const loadedEntry = await apiClient.getKnowledgeEntry(entryId);
        if (cancelled) return;
        setEntry(loadedEntry);

        if (loadedEntry.project_id !== null) {
          // Same listProjects() + find-by-id workaround already
          // established in ConversationList.tsx for the missing
          // GET /api/projects/{id} — reused here, not reinvented.
          const projects = await apiClient.listProjects();
          if (!cancelled) {
            setProject(
              projects.find((p) => p.id === loadedEntry.project_id) ?? null
            );
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load knowledge entry."
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
  }, [entryId]);

  if (loading) return <p>Loading knowledge entry...</p>;
  if (error) return <p className="text-red-600">Error: {error}</p>;
  if (!entry) return <p>Knowledge entry not found.</p>;

  const contentEntries = entry.content ? Object.entries(entry.content) : [];

  return (
    <div className="w-full max-w-2xl mx-auto flex flex-col gap-3">
      <h1 className="text-2xl font-bold">{entry.title}</h1>

      <div className="text-sm text-gray-500">
        {entry.entry_type} —{" "}
        {entry.project_id === null ? (
          "General"
        ) : (
          <Link
            href={`/projects/${entry.project_id}/chat`}
            className="underline"
          >
            {project ? project.title : `Project #${entry.project_id}`}
          </Link>
        )}
      </div>

      <p>{entry.summary}</p>

      {/* content — hidden if null/empty. Same generic key/value rendering
          EngineeringGuidanceView.tsx uses for preliminary_calculations;
          String(value) is a deliberately simple stand-in for nested
          arrays/objects (e.g. a design_pattern's "alternatives_considered"
          list) — readable but not pretty. Not fixed now, matching
          Sprint 5 planning's stance of leaving content's internal shape
          unenforced until real usage patterns solidify. */}
      {contentEntries.length > 0 && (
        <div className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-gray-600">Details</span>
          <div className="border rounded divide-y">
            {contentEntries.map(([key, value]) => (
              <div
                key={key}
                className="flex justify-between px-3 py-1 text-sm"
              >
                <span className="text-gray-600">{key}</span>
                <span>{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* tags — hidden if null/empty. Display only; no filtering, no
          editing, per approved scope. */}
      {entry.tags && entry.tags.length > 0 && (
        <div className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-gray-600">Tags</span>
          <div className="flex gap-2 flex-wrap">
            {entry.tags.map((tag) => (
              <span key={tag} className="text-xs bg-gray-100 rounded px-2 py-1">
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* No provenance UI for source_conversation_id/source_message_id —
          deferred per Sprint 6 planning decision 2. */}

      <div className="text-xs text-gray-400">
        Created {new Date(entry.created_at).toLocaleString()}
      </div>
    </div>
  );
}
