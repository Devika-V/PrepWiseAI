import { useState } from "react";
import { startInterview } from "../api";

// Must exactly match the role/company combinations that actually exist in
// your backend's data/questions.json. Each role only lists the companies it
// genuinely has questions for, so picking any combo here is guaranteed to work.
const ROLE_COMPANIES = {
  "Software Engineer": ["Goldman Sachs", "Google", "Amazon", "Microsoft", "Meta", "JPMorgan Chase"],
  "Data Analyst": ["Goldman Sachs", "Amazon"],
  "Product Manager": ["Google", "Amazon"],
  "Investment Banking Analyst": ["Goldman Sachs", "JPMorgan Chase"],
  "Marketing Analyst": ["Amazon", "Meta"],
};
const ROLES = Object.keys(ROLE_COMPANIES);

export default function Dashboard({ token, onStart }) {
  const [role, setRole] = useState(ROLES[0]);
  const [company, setCompany] = useState(ROLE_COMPANIES[ROLES[0]][0]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleRoleChange(newRole) {
    setRole(newRole);
    setCompany(ROLE_COMPANIES[newRole][0]); // reset to a valid company whenever the role changes
  }

  async function handleStart() {
    setError("");
    setLoading(true);
    try {
      const data = await startInterview(token, role, company);
      onStart(data.session_id, role, company, data.question);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2 className="font-display text-3xl mb-2">Ready when you are.</h2>
      <p className="text-muted mb-8">
        Pick a target role and company - questions and grading adapt to both, and to your past performance.
      </p>

      <div className="bg-white border border-ink/10 rounded-lg p-6 space-y-5">
        <div>
          <label className="block text-xs uppercase tracking-wide text-muted mb-1">Role</label>
          <select
            value={role}
            onChange={(e) => handleRoleChange(e.target.value)}
            className="w-full border border-ink/20 rounded-md px-3 py-2 bg-white"
          >
            {ROLES.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs uppercase tracking-wide text-muted mb-1">Company</label>
          <select
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            className="w-full border border-ink/20 rounded-md px-3 py-2 bg-white"
          >
            {ROLE_COMPANIES[role].map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        {error && <p className="text-weak text-sm">{error}</p>}

        <button
          onClick={handleStart}
          disabled={loading}
          className="w-full bg-accent text-ink font-semibold rounded-md py-2.5 hover:bg-accent/90 transition-colors disabled:opacity-50"
        >
          {loading ? "Setting up..." : "Start mock interview"}
        </button>
      </div>
    </div>
  );
}