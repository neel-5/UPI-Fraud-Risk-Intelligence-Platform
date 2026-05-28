const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json();
}

export const api = {
  overview: () => request("/overview"),
  accounts: (params = {}) => {
    const search = new URLSearchParams(params);
    return request(`/accounts?${search.toString()}`);
  },
  account: (accountId) => request(`/accounts/${accountId}`),
  graph: (params = {}) => {
    const search = new URLSearchParams(params);
    return request(`/graph?${search.toString()}`);
  },
  heatmap: () => request("/heatmap"),
  cases: () => request("/cases"),
  simulate: (payload) =>
    request("/simulate", {
      method: "POST",
      body: JSON.stringify(payload)
    })
};
