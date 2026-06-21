import { useState } from "react";
import { submitAnswer } from "../api";

export default function InterviewScreen({ token, session, onFinish }) {
  const [question, setQuestion] = useState(session.question);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState(null); // { score, feedback }
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [questionCount, setQuestionCount] = useState(1);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!answer.trim()) return;
    setError("");
    setLoading(true);
    try {
      const data = await submitAnswer(token, session.sessionId, answer);
      setResult({ score: data.score, feedback: data.feedback });
      // Give the person a few seconds to actually read the feedback before
      // the next question replaces it.
      setTimeout(() => {
        setQuestion(data.next_question);
        setAnswer("");
        setResult(null);
        setQuestionCount((c) => c + 1);
      }, 3500);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const stampColor = result
    ? result.score >= 7
      ? "border-good text-good"
      : result.score >= 4
      ? "border-accent text-accent"
      : "border-weak text-weak"
    : "";

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <span className="text-xs uppercase tracking-wide text-muted">
          {session.role} - {session.company} - Question {questionCount}
        </span>
        <button onClick={onFinish} className="text-sm text-muted hover:text-ink underline">
          End &amp; view report
        </button>
      </div>

      <div className="bg-white border border-ink/10 rounded-lg p-6 mb-6">
        <span className="inline-block text-xs font-mono uppercase bg-ink/5 text-ink/70 px-2 py-1 rounded mb-3">
          {question.skill_tag}
        </span>
        <p className="font-display text-xl leading-snug">{question.text}</p>
      </div>

      {result ? (
        <div className="bg-white border border-ink/10 rounded-lg p-6 flex items-start gap-5">
          <div
            className={`shrink-0 w-20 h-20 rounded-full border-4 ${stampColor} flex flex-col items-center justify-center -rotate-6 font-mono`}
            style={{ borderStyle: "double" }}
          >
            <span className="text-2xl font-bold leading-none">{result.score}</span>
            <span className="text-[10px] tracking-wide">/ 10</span>
          </div>
          <div>
            <p className="text-sm font-medium text-muted mb-1">Feedback</p>
            <p className="text-ink">{result.feedback}</p>
            <p className="text-xs text-muted mt-3">Next question loading...</p>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={6}
            required
            placeholder="Type your answer as you would say it out loud..."
            className="w-full border border-ink/20 rounded-md px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-accent resize-none"
          />
          {error && <p className="text-weak text-sm mt-2">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="mt-4 bg-ink text-paper rounded-md py-2.5 px-6 font-medium hover:bg-ink/90 transition-colors disabled:opacity-50"
          >
            {loading ? "Grading..." : "Submit answer"}
          </button>
        </form>
      )}
    </div>
  );
}