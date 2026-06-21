import { useState } from "react";
import AuthForm from "./components/AuthForm";
import Dashboard from "./components/Dashboard";
import InterviewScreen from "./components/InterviewScreen";
import ReportScreen from "./components/ReportScreen";

export default function App() {
  // sessionStorage (not localStorage) so the token survives a page refresh
  // but disappears when the tab is closed - a reasonable middle ground for
  // a demo project. Never store anything more sensitive than this token here.
  const [token, setToken] = useState(() => sessionStorage.getItem("token") || "");
  const [view, setView] = useState(token ? "dashboard" : "auth");
  const [session, setSession] = useState(null); // { sessionId, role, company, question }

  function handleAuthSuccess(newToken) {
    sessionStorage.setItem("token", newToken);
    setToken(newToken);
    setView("dashboard");
  }

  function handleLogout() {
    sessionStorage.removeItem("token");
    setToken("");
    setSession(null);
    setView("auth");
  }

  function handleInterviewStarted(sessionId, role, company, question) {
    setSession({ sessionId, role, company, question });
    setView("interview");
  }

  function handleViewReport() {
    setView("report");
  }

  function handleBackToDashboard() {
    setSession(null);
    setView("dashboard");
  }

  return (
    <div className="min-h-screen bg-paper text-ink font-body">
      <header className="border-b border-ink/10 px-6 py-4 flex items-center justify-between">
        <h1 className="font-display text-2xl tracking-tight">
          PrepWise <span className="text-accent">AI</span>
        </h1>
        {token && (
          <button onClick={handleLogout} className="text-sm text-muted hover:text-ink transition-colors">
            Log out
          </button>
        )}
      </header>

      <main className="max-w-3xl mx-auto px-6 py-10">
        {view === "auth" && <AuthForm onSuccess={handleAuthSuccess} />}

        {view === "dashboard" && token && (
          <Dashboard token={token} onStart={handleInterviewStarted} />
        )}

        {view === "interview" && token && session && (
          <InterviewScreen token={token} session={session} onFinish={handleViewReport} />
        )}

        {view === "report" && token && session && (
          <ReportScreen token={token} session={session} onBack={handleBackToDashboard} />
        )}
      </main>
    </div>
  );
}