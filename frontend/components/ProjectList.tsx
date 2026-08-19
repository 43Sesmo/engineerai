"use client";

import { useEffect, useState, FormEvent, ChangeEvent } from "react";
import Link from "next/link";
import { apiClient, Project } from "../lib/api-client";

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const result = await apiClient.listProjects();
        if (!cancelled) {
          setProjects(result);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load projects."
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
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;

    setCreating(true);
    setError(null);
    try {
      const project = await apiClient.createProject({ title });
      setProjects((prev) => [...prev, project]);
      setTitle("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="w-full max-w-xl">
      <form onSubmit={handleCreate} className="flex gap-2 mb-6">
        <input
          type="text"
          value={title}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)}
          placeholder="New project title"
          className="flex-1 border rounded px-3 py-2"
          disabled={creating}
        />
        <button
          type="submit"
          disabled={creating}
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          {creating ? "Creating..." : "Create"}
        </button>
      </form>

      {error && <p className="text-red-600 mb-4">{error}</p>}

      {loading ? (
        <p>Loading projects...</p>
      ) : projects.length === 0 ? (
        <p>No projects yet.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {projects.map((project) => (
            <li key={project.id} className="border rounded px-3 py-2">
              <Link
                href={`/projects/${project.id}/chat`}
                className="font-semibold text-blue-600 underline"
              >
                {project.title}
              </Link>
              <span className="text-sm text-gray-500 ml-2">
                ({project.status})
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
