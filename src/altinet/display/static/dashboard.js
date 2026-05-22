const ROOM_NAMES = [
  'Kitchen', 'Dining Room', 'Living Room', 'Bedroom 1', 'Bathroom', 'Laundry', 'Office', 'Entry'
];
console.log("Altinet dashboard.js loaded");



function getEl(id) {
  const el = document.getElementById(id);
  if (!el) {
    console.warn(`Missing dashboard element: ${id}`);
  }
  return el;
}

function showAddUserForm() {
  const form = getEl('add-user-form');
  if (!form) return;
  form.hidden = false;
  getEl('user-display-name')?.focus();
  setDashboardStatus('Add User form shown');
}

function hideAddUserForm() {
  const form = getEl('add-user-form');
  if (!form) return;
  form.reset();
  form.hidden = true;
  setDashboardStatus('Add User cancelled');
}

async function saveUser(event) {
  event.preventDefault();
  const form = event.target;
  const displayName = form.display_name.value?.trim();
  if (!displayName) {
    setDashboardStatus('Display name is required');
    return;
  }
  const payload = {
    display_name: displayName,
    preferred_name: form.preferred_name.value || null,
    access_level: form.access_level.value || 'resident_standard',
    contextual_information: form.contextual_information.value || null,
  };
  setDashboardStatus('Saving user...');
  try {
    const response = await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const errorText = await response.text();
      setDashboardStatus(`Save failed (${response.status}): ${errorText}`);
      console.error('Failed to save user', { status: response.status, errorText });
      return;
    }
    await response.json();
    await loadUsers();
    form.reset();
    form.access_level.value = 'resident_standard';
    form.hidden = true;
    setDashboardStatus('User saved');
  } catch (error) {
    console.error('Failed to save user', error);
    setDashboardStatus(`Save failed: ${error.message}`);
  }
}

async function seedDemoUsers() {
  const seedButton = getEl('seed-demo-users-button');
  const dashboardStatusEl = getEl('dashboard-status');
  if (!seedButton) return;
  console.log('Seed demo users button clicked');
  if (dashboardStatusEl) dashboardStatusEl.textContent = 'Seeding demo users...';
  seedButton.disabled = true;
  try {
    const response = await fetch('/api/registry/seed-demo', { method: 'POST' });
    if (!response.ok) throw new Error(`Seed API failed (${response.status})`);
    const payload = await response.json();
    if (dashboardStatusEl) dashboardStatusEl.textContent = payload.message || 'Demo data seeded';
    await loadUsers();
  } catch (error) {
    console.error('Failed to seed demo users', error);
    if (dashboardStatusEl) dashboardStatusEl.textContent = `Failed to seed demo users: ${error.message}`;
  } finally {
    seedButton.disabled = false;
  }
}

function setDashboardStatus(message) {
  const statusEl = document.getElementById('dashboard-status');
  if (statusEl) statusEl.textContent = message;
}

function asText(value, fallback) {
  if (value === null || value === undefined || value === '') return fallback;
  return typeof value === 'string' ? value : JSON.stringify(value);
}

function safeArray(value, fallback = []) {
  return Array.isArray(value) ? value : fallback;
}

function fallbackState() {
  return {
    system_status: 'All systems operational',
    residents: [],
    devices: [],
    agents: [{ name: 'R1 - Atlas', status: 'monitoring' }],
    decisions: [],
    alerts: [],
    runtime_state: {},
  };
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
  console.log('Loading users...');
  setDashboardStatus('Loading users...');
  try {
    const response = await fetch('/api/users');
    if (!response.ok) throw new Error(`GET /api/users failed (${response.status})`);
    const payload = await response.json();
    const users = Array.isArray(payload) ? payload : (Array.isArray(payload?.users) ? payload.users : []);
    console.log('Users response:', users);
    window.__loadedUsers = users;
    window.__usersLoaded = true;
    setDashboardStatus(`Loaded ${window.__loadedUsers.length} users`);
  } catch (error) {
    console.error('Failed to load users', error);
    window.__loadedUsers = [];
    window.__usersLoaded = true;
    setDashboardStatus(`Failed to load users: ${error.message}`);
  }
  renderUsers(window.__loadedUsers);
}




function formatContextualInformation(contextualInformation) {
  if (!contextualInformation) return '';
  if (typeof contextualInformation === 'string') return contextualInformation.trim();
  if (Array.isArray(contextualInformation)) {
    return contextualInformation.map((item) => {
      if (typeof item === 'string') return item;
      return item?.summary || item?.note || JSON.stringify(item);
    }).filter(Boolean).join(' · ');
  }
  return JSON.stringify(contextualInformation);
}

function renderUsers(users) {
  const residentsEl = document.getElementById('users-list');
  if (!residentsEl) {
    setDashboardStatus('Missing required DOM element: users-list');
    return;
  }
  if (!users || users.length === 0) {
    residentsEl.innerHTML = '<li class="empty-users">No users added yet.</li>';
    return;
  }
  residentsEl.innerHTML = users.map((u) => {
    const contextualInformation = formatContextualInformation(u.contextual_information);
    return `<li class="user-card">
      <div class="user-row"><strong class="user-name">${u.display_name || 'Unknown User'}</strong><span class="badge access">${u.access_level || 'unknown'}</span>${u.category ? `<span class="badge category">${u.category}</span>` : ''}</div>
      <div class="user-meta">${u.preferred_name ? `Preferred: ${u.preferred_name}` : 'Preferred: not set'}</div>
      ${contextualInformation ? `<div class="user-context">Context: ${contextualInformation}</div>` : ''}
      ${u.notes ? `<div class="user-notes">Notes: ${u.notes}</div>` : ''}
    </li>`;
  }).join('');
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


async function loadWeather() {
  const placeholderEl = getEl('weather-placeholder');
  const detailsEl = getEl('weather-details');
  if (!placeholderEl || !detailsEl) return;

  placeholderEl.textContent = 'Loading weather...';
  detailsEl.innerHTML = '';

  try {
    const response = await fetch('/api/weather/current');
    if (!response.ok) throw new Error(`Weather API failed (${response.status})`);

    const payload = await response.json();
    if (!payload?.available) {
      placeholderEl.textContent = payload?.message || 'Set and verify home address to enable weather.';
      return;
    }

    const temp = payload.temperature;
    const description = payload.weather_description || 'Current conditions unavailable';
    const location = payload.location_name || 'Unknown location';

    placeholderEl.textContent = `${location} · ${temp ?? '--'}°C · ${description}`;
    detailsEl.innerHTML = [
      `<p>Feels like: ${payload.apparent_temperature ?? '--'}°C</p>`,
      `<p>Humidity: ${payload.humidity ?? '--'}%</p>`,
      `<p>Precipitation: ${payload.precipitation ?? '--'} mm</p>`,
      `<p>Wind: ${payload.wind_speed ?? '--'} km/h</p>`,
    ].join('');
  } catch (error) {
    console.error('Failed to load weather', error);
    placeholderEl.textContent = 'Unable to fetch weather right now.';
  }
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
  const now = new Date();
  document.getElementById('current-time').textContent = now.toLocaleTimeString();
  document.getElementById('header-date').textContent = now.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

  try {
    const response = await fetch('/api/state');
    if (!response.ok) throw new Error(`State API failed (${response.status})`);
    const data = await response.json();
    document.getElementById('system-status').textContent = asText(data?.system_status, 'waiting_for_runtime');

    const residents = extractResidents(data);
    const usersListEl = document.getElementById('users-list');
    if (usersListEl && !window.__usersLoaded && !usersListEl.innerHTML) {
      usersListEl.innerHTML = residents.map((r) => `<li>${r}</li>`).join('') || '<li>No residents available.</li>';
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
  } catch (error) {
    console.error('Failed to load state', error);
    const data = fallbackState();
    document.getElementById('system-status').textContent = 'All systems operational (fallback mode)';
    document.getElementById('decisions-list').innerHTML = '<div class="decision-item">No recent decisions.</div>';
    renderFloorplan(data);
    renderBottomCards(data);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  console.log("Altinet dashboard DOM ready");

  try { refreshState(); } catch (error) { console.error('refreshState startup failed', error); }
  try { setInterval(refreshState, 2000); } catch (error) { console.error('refreshState interval failed', error); }
  try { loadUsers(); } catch (error) { console.error('loadUsers startup failed', error); }

  const assistantSend = getEl('assistant-send');
  assistantSend?.addEventListener('click', async () => {
    const input = getEl('assistant-input');
    const text = input?.value || '';
    if (!text.trim()) return;
    appendAssistantMessage('user', text.trim());
    input.value = '';
    try {
      const payload = await sendAssistantMessage(text.trim());
      appendAssistantMessage('assistant', payload.reply || "I'm here to help.");
      const modeEl = getEl('assistant-mode');
      if (modeEl) modeEl.textContent = payload.used_openai ? 'using OpenAI' : 'local fallback';
      renderSuggestedUpdates(payload.suggested_profile_updates || []);
    } catch (_error) {
      appendAssistantMessage('assistant', 'I hit a temporary issue. Using local fallback response.');
      const modeEl = getEl('assistant-mode');
      if (modeEl) modeEl.textContent = 'local fallback';
    }
  });

  const requiredElements = [
    'dashboard-status', 'users-list', 'add-user-button', 'add-user-form', 'user-display-name',
    'user-preferred-name', 'user-access-level', 'user-contextual-information', 'save-user-button', 'cancel-user-button'
  ];
  const missingRequired = requiredElements.filter((id) => !document.getElementById(id));
  if (missingRequired.length > 0) setDashboardStatus(`Missing required DOM element(s): ${missingRequired.join(', ')}`);

  getEl('add-user-button')?.addEventListener('click', showAddUserForm);
  getEl('cancel-user-button')?.addEventListener('click', hideAddUserForm);
  getEl('save-user-button')?.addEventListener('click', (event) => {
    event.preventDefault();
    getEl('add-user-form')?.requestSubmit();
  });
  getEl('add-user-form')?.addEventListener('submit', saveUser);
  getEl('seed-demo-users-button')?.addEventListener('click', seedDemoUsers);
  getEl('ahlan-send-button')?.addEventListener('click', () => {
    getEl('assistant-send')?.click();
  });

  try { loadWeather(); } catch (error) { console.error('loadWeather startup failed', error); }
});

