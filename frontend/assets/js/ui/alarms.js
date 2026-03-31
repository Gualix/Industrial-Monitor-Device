export function updateSystemStatus(element, system) {
  const active = Boolean(system?.sensors?.alarms?.active);
  element.textContent = active ? 'Alarm Active' : 'System Normal';
  element.style.color = active ? 'var(--danger)' : 'var(--ok)';
}
