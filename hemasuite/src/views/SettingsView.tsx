import { useEffect, useState } from "react";
import { api } from "../hooks/useApi";

interface Settings {
  r_path: string;
  python_path: string;
  output_dir: string;
  theme: string;
  default_journal: string;
}

export function SettingsView() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api<Settings>("/settings").then(setSettings);
  }, []);

  const update = async (field: keyof Settings, value: string) => {
    if (!settings) return;
    const updated = { ...settings, [field]: value };
    setSettings(updated);
    setSaving(true);
    setSaved(false);
    await api<Settings>("/settings", {
      method: "PATCH",
      body: JSON.stringify({ [field]: value }),
    });
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (!settings) return <div className="text-gray-400 text-sm">Loading...</div>;

  const fields: { key: keyof Settings; label: string; placeholder: string }[] = [
    { key: "r_path", label: "Rscript Path", placeholder: "Rscript" },
    { key: "python_path", label: "Python Path", placeholder: "python3" },
    { key: "output_dir", label: "Output Directory", placeholder: "~/HemaSuite/output" },
    { key: "default_journal", label: "Default Journal", placeholder: "e.g. Blood, JCO" },
  ];

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Settings</h2>
        {saving && <span className="text-sm text-gray-400">Saving...</span>}
        {saved && <span className="text-sm text-green-600">Saved</span>}
      </div>

      <div className="p-4 bg-white rounded-lg border space-y-4">
        {fields.map(({ key, label, placeholder }) => (
          <div key={key}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {label}
            </label>
            <input
              type="text"
              value={settings[key]}
              placeholder={placeholder}
              onChange={(e) => update(key, e.target.value)}
              className="w-full px-3 py-2 border rounded-md text-sm"
            />
          </div>
        ))}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Theme
          </label>
          <select
            value={settings.theme}
            onChange={(e) => update("theme", e.target.value)}
            className="w-full px-3 py-2 border rounded-md text-sm"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
      </div>
    </div>
  );
}
