function asText(value, fallback) {
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'string') return value;
  return JSON.stringify(value, null, 2);
}

async function refreshState() {
  try {
    const response = await fetch('/api/state');
    const data = await response.json();

    document.getElementById('current-time').textContent = new Date(data.current_time).toLocaleString();
    document.getElementById('system-status').textContent = asText(data.system_status, 'Status unavailable.');
    document.getElementById('runtime-state').textContent = asText(data.runtime_state, 'Runtime state not available yet.');
    document.getElementById('room-context').textContent = asText(data.room_context, 'Room context not available yet.');
    document.getElementById('recent-events').textContent = asText(data.recent_events, 'No recent events.');
    document.getElementById('latest-decision').textContent = asText(data.latest_decision, 'No decision has been recorded yet.');
    document.getElementById('decision-explanation').textContent = asText(data.decision_explanation, '');
    document.getElementById('perception-summary').textContent = asText(data.perception_summary, 'Perception summary not available yet.');

    const captureImage = document.getElementById('latest-capture');
    const capturePlaceholder = document.getElementById('capture-placeholder');
    if (data.capture_available) {
      captureImage.style.display = 'block';
      captureImage.src = '/captures/latest.jpg?ts=' + Date.now();
      capturePlaceholder.textContent = '';
    } else {
      captureImage.style.display = 'none';
      capturePlaceholder.textContent = 'No capture image available yet.';
    }
  } catch (_error) {
    document.getElementById('system-status').textContent = 'Unable to fetch dashboard state.';
  }
}

refreshState();
setInterval(refreshState, 2000);
