import { useEffect, useState } from "react";
import { getReport } from "../api";

export default function ReportScreen({ token, session, onBack }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getReport(token, session.sessionId).then(setReport).catch((err) => setError(err.message));
  }, [token, session.sessionId]);

  if (error) return <p className="text-weak">{error}</p>;
  if (!report) return <p className="text-muted">Loading your report...</p>;

  return (
    <div>
      <h2 className="font-display text-3xl mb-2">Your skill snapshot</h2>
      <p className="text-muted mb-8">Based on every question you've answered so far, not just this session.</p>

      <div className="bg-white border border-ink/10 rounded-lg p-6 space-y-4 mb-8">
        {report.skill_breakdown.map((s) => (
          <div key={s.skill_tag}>
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium">{s.skill_tag}</span>
              <span className="font-mono text-muted">
                {s.attempts === 0 ? "no attempts yet" : `${s.avg_score} / 10`}
              </span>
            </div>
            <div className="h-2 bg-ink/10 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  s.avg_score >= 7 ? "bg-good" : s.avg_score >= 4 ? "bg-accent" : "bg-weak"
                }`}
                style={{ width: `${Math.max(4, (s.avg_score / 10) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {report.focus_areas.length > 0 && (
        <div>
          <h3 className="font-display text-xl mb-3">Where to focus next</h3>
          <div className="space-y-3">
            {report.focus_areas.map((f) => (
              <div key={f.skill_tag} className="border border-ink/10 rounded-lg p-4 bg-white">
                <p className="font-medium mb-1">
                  {f.skill_tag} <span className="font-mono text-muted text-sm">({f.avg_score}/10)</span>
                </p>
                <p className="text-sm text-muted">{f.recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <button onClick={onBack} className="mt-8 text-sm text-muted hover:text-ink underline">
        Back to dashboard
      </button>
    </div>
  );
}