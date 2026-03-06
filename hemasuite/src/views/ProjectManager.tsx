import { useEffect, useState } from "react";
import { api } from "../hooks/useApi";

interface Project {
  name: string;
  slug: string;
  description: string;
  created_at: string;
}

export function ProjectManager() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api<Project[]>("/projects")
      .then(setProjects)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!newName.trim()) return;
    await api<Project>("/projects", {
      method: "POST",
      body: JSON.stringify({ name: newName, description: newDesc }),
    });
    setNewName("");
    setNewDesc("");
    load();
  };

  const remove = async (slug: string) => {
    if (!confirm(`Delete project "${slug}"?`)) return;
    await api(`/projects/${slug}`, { method: "DELETE" });
    load();
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <h2 className="text-xl font-semibold">Projects</h2>

      <div className="p-4 bg-white rounded-lg border space-y-3">
        <h3 className="text-sm font-medium text-gray-700">New Project</h3>
        <input
          type="text"
          placeholder="Project name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          className="w-full px-3 py-2 border rounded-md text-sm"
        />
        <input
          type="text"
          placeholder="Description (optional)"
          value={newDesc}
          onChange={(e) => setNewDesc(e.target.value)}
          className="w-full px-3 py-2 border rounded-md text-sm"
        />
        <button
          onClick={create}
          disabled={!newName.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          Create Project
        </button>
      </div>

      {loading ? (
        <div className="text-gray-400 text-sm">Loading...</div>
      ) : projects.length === 0 ? (
        <div className="text-gray-400 text-sm">No projects yet. Create one above.</div>
      ) : (
        <div className="space-y-2">
          {projects.map((p) => (
            <div
              key={p.slug}
              className="p-4 bg-white rounded-lg border flex items-center justify-between"
            >
              <div>
                <h3 className="font-medium">{p.name}</h3>
                {p.description && (
                  <p className="text-sm text-gray-500">{p.description}</p>
                )}
                <p className="text-xs text-gray-400 mt-1">
                  Created {new Date(p.created_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={() => remove(p.slug)}
                className="text-sm text-red-500 hover:text-red-700"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
