// Change this if your backend runs somewhere other than localhost:8000.
const API_BASE = "http://localhost:8000";

async function request(path, { method = "GET", body, token, isForm = false } = {}) {
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let payload = body;
  if (body && !isForm) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  // When isForm is true, payload stays as the URLSearchParams object the
  // caller built - the browser sets the correct Content-Type for that
  // automatically, which is what FastAPI's login form expects.

  const res = await fetch(`${API_BASE}${path}`, { method, headers, body: payload });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export function registerUser(email, password) {
  return request("/register", { method: "POST", body: { email, password } });
}

export function loginUser(email, password) {
  const form = new URLSearchParams();
  form.append("username", email); // FastAPI's login form always calls this field "username"
  form.append("password", password);
  return request("/login", { method: "POST", body: form, isForm: true });
}

export function startInterview(token, role, company) {
  return request("/interview/start", { method: "POST", token, body: { role, company } });
}

export function submitAnswer(token, sessionId, answerText) {
  return request(`/interview/${sessionId}/answer`, {
    method: "POST",
    token,
    body: { answer_text: answerText },
  });
}

export function getReport(token, sessionId) {
  return request(`/interview/${sessionId}/report`, { token });
}