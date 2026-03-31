async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || 'Request failed');
  }
  return payload;
}

export function getSystemState() {
  return requestJson('/api/state');
}

export function getSettings() {
  return requestJson('/api/settings');
}

export function resetMaintenance(password) {
  return requestJson('/api/runtime/reset-maintenance', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  });
}
