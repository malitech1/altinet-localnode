const ROOM_NAMES = [
  'Kitchen', 'Dining Room', 'Living Room', 'Bedroom 1', 'Bathroom', 'Laundry', 'Office', 'Entry'
];

function asText(value, fallback) {
  if (value === null || value === undefined || value === '') return fallback;
  return typeof value === 'string' ? value : JSON.stringify(value);
}

function safeArray(value, fallback = []) {
  return Array.isArray(value) ? value : fallback;
}

function extractResidents(data) {
  return safeArray(data?.residents, []).map((r) => r?.name || 'Resident');
}

function renderAssistantMessages() {
  const chat = document.getElementById('assistant-chat');
  if (!chat) return;
  const messages = window.__ahlanMessages || [];
  chat.innerHTML = messages.map((m) => `<div class="chat-message ${m.role}"><strong>${m.role === 'assistant' ? 'AHLAN' : 'You'}:</strong> ${m.content}</div>`).join('');
}

function appendAssistantMessage(role, content) {
  if (!window.__ahlanMessages) window.__ahlanMessages = [];
  window.__ahlanMessages.push({ role, content });
  renderAssistantMessages();
}

async function loadUsers() {
  const response = await fetch('/api/users');
  const users = await response.json();
  window.__loadedUsers = users;
  const residentsEl = document.getElementById('residents-list');
  if (residentsEl) {
    residentsEl.innerHTML = users.map((u) => `<li>${u.display_name} · ${u.role} · ${u.access_level} · status: active</li>`).join('') || '<li>No users yet.</li>';
  }
}


function selectedUserId() {
  const first = (window.__loadedUsers || [])[0];
  return first?.id || null;
}

function renderSuggestedUpdates(updates) {
  const panel = document.getElementById('assistant-suggestions');
  if (!panel) return;
  if (!updates || updates.length === 0) {
    panel.innerHTML = '';
    return;
  }
  panel.innerHTML = `<strong>AHLAN thinks it learned something</strong>${updates.map((u) => `<div class="suggestion-item">${u.type}: ${u.summary} (${Math.round((u.confidence || 0) * 100)}%)</div>`).join('')}`;
}

async function sendAssistantMessage(text) {
  const response = await fetch('/api/assistant/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text, user_id: selectedUserId() }),
  });
  return response.json();
}

function roomForEntity(entity, index) {
  const room = entity?.room || entity?.location || ROOM_NAMES[index % ROOM_NAMES.length];
  return ROOM_NAMES.includes(room) ? room : ROOM_NAMES[index % ROOM_NAMES.length];
}

function renderFloorplan(data) {
  const floorEl = document.getElementById('floorplan-grid');
  if (!floorEl) return;
  const residents = safeArray(data?.residents, []).map((r, i) => ({ name: r.name || 'Resident', room: r.location || ROOM_NAMES[i % ROOM_NAMES.length] }));
  const devices = safeArray(data?.devices, []).map((d, i) => ({ name: d.name || 'Device', room: d.room || ROOM_NAMES[(i + 2) % ROOM_NAMES.length] }));
  const agents = safeArray(data?.agents, []).map((a, i) => ({ name: a.name || 'Agent', room: a.room || ROOM_NAMES[(i + 4) % ROOM_NAMES.length] }));

  const html = ROOM_NAMES.map((room) => {
    const rs = residents.filter((r) => roomForEntity(r, 0) === room).map((r) => `<span class="marker resident"><i class="dot resident"></i>${r.name}</span>`).join('');
    const ds = devices.filter((d, i) => roomForEntity(d, i) === room).map((d) => `<span class="marker device"><i class="dot device"></i>${d.name}</span>`).join('');
    const ags = agents.filter((a, i) => roomForEntity(a, i) === room).map((a) => `<span class="marker agent"><i class="dot agent"></i>${a.name}</span>`).join('');
    return `<article class="room"><div class="room-title">${room}</div>${rs}${ds}${ags}</article>`;
  }).join('');

  floorEl.innerHTML = html;
}

function renderBottomCards(data) {
  const el = document.getElementById('bottom-cards');
  if (!el) return;
  const cards = [
    ['Agents', safeArray(data?.agents, []).map((a) => a.name).join(', ') || 'No active agents'],
    ['Appliances', safeArray(data?.devices, []).map((d) => `${d.name} (${d.state})`).join(', ') || 'No appliances'],
    ['Active Alerts', safeArray(data?.alerts, ['No active alerts']).join(', ')],
    ['Energy Usage', asText(data?.runtime_state?.energy_usage, '4.1 kWh · Placeholder')],
    ['Indoor Climate', asText(data?.runtime_state?.indoor_climate, '21°C · 46% humidity')],
  ];
  el.innerHTML = cards.map(([title, value]) => `<article class="stat-card"><h4>${title}</h4><div class="stat-value">${value}</div></article>`).join('');
}

async function refreshState() {
  try {
    const response = await fetch('/api/state');
    const data = await response.json();
    const now = data?.current_time ? new Date(data.current_time) : new Date();

    document.getElementById('current-time').textContent = now.toLocaleTimeString();
    document.getElementById('header-date').textContent = now.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
    document.getElementById('system-status').textContent = asText(data?.system_status, 'waiting_for_runtime');

    const residents = extractResidents(data);
    if (!document.getElementById('residents-list').innerHTML) {
      document.getElementById('residents-list').innerHTML = residents.map((r) => `<li>${r}</li>`).join('') || '<li>No residents available.</li>';
    }

    const decisions = safeArray(data?.decisions, []);
    document.getElementById('decisions-list').innerHTML = decisions.map((d) => {
      const action = asText(d?.action || d?.selected_action, 'no action');
      const explanation = asText(d?.explanation || d?.rationale, 'No explanation available.');
      const impact = asText(d?.impact, 'Impact not recorded.');
      const time = asText(d?.timestamp || d?.time, 'Time unavailable');
      return `<div class="decision-item"><strong>${action}</strong><br/>${time}<br/>${explanation}<br/><em>${impact}</em></div>`;
    }).join('') || '<div class="decision-item">No recent decisions.</div>';

    renderFloorplan(data);
    renderBottomCards(data);
  } catch (_error) {
    document.getElementById('system-status').textContent = 'Unable to fetch dashboard state.';
  }
}

refreshState();
setInterval(refreshState, 2000);

loadUsers();

document.getElementById('assistant-send')?.addEventListener('click', async () => {
  const input = document.getElementById('assistant-input');
  const text = input?.value || '';
  if (!text.trim()) return;
  appendAssistantMessage('user', text.trim());
  input.value = '';
  try {
    const payload = await sendAssistantMessage(text.trim());
    appendAssistantMessage('assistant', payload.reply || 'I'm here to help.');
    const modeEl = document.getElementById('assistant-mode');
    if (modeEl) modeEl.textContent = payload.used_openai ? 'using OpenAI' : 'local fallback';
    renderSuggestedUpdates(payload.suggested_profile_updates || []);
  } catch (_error) {
    appendAssistantMessage('assistant', 'I hit a temporary issue. Using local fallback response.');
  }
});

const dialog = document.getElementById('add-user-dialog');
document.getElementById('open-add-user')?.addEventListener('click', () => dialog?.showModal());
document.getElementById('cancel-add-user')?.addEventListener('click', () => dialog?.close());
document.getElementById('add-user-form')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.target;
  const payload = {
    display_name: form.display_name.value,
    preferred_name: form.preferred_name.value,
    role: form.role.value,
    access_level: form.access_level.value,
    notes: form.notes.value || null,
  };
  await fetch('/api/users', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  dialog?.close();
  form.reset();
  loadUsers();
});
