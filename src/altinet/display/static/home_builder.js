let homeModel = null;
const modeDefs = ["select", "draw_wall", "erase_wall", "define_room", "place_door", "place_light", "place_pod", "pan"];
let mode = "select";
let selectedFloorId = null;
let wallStart = null;
let previewPoint = null;
let roomPoints = [];

function v(id) { return document.getElementById(id); }
function uid(prefix) { return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 1000)}`; }
function snap(n) { return Math.round(n * 2) / 2; }
function floorItems() { return homeModel.floors.filter((f) => f.id === selectedFloorId); }

function mapFormToModel(model) {
  model.property_name = v('property_name').value;
  model.property_boundary.width = Number(v('boundary_width').value);
  model.property_boundary.depth = Number(v('boundary_depth').value);
  model.house_dimensions.width = Number(v('house_width').value);
  model.house_dimensions.depth = Number(v('house_depth').value);
}
function fillForm(model) { v('property_name').value = model.property_name; v('boundary_width').value = model.property_boundary.width; v('boundary_depth').value = model.property_boundary.depth; v('house_width').value = model.house_dimensions.width; v('house_depth').value = model.house_dimensions.depth; }
function floorName() { const floor = homeModel.floors.find((f) => f.id === selectedFloorId); return floor ? floor.name : 'Unknown Floor'; }

function renderFloorSelect() {
  const select = v('floor-select');
  select.innerHTML = homeModel.floors.map((f) => `<option value="${f.id}">${f.name}</option>`).join('');
  select.value = selectedFloorId;
}

function coordFromEvent(evt) {
  const svg = v('floorplan'); const rect = svg.getBoundingClientRect();
  const x = ((evt.clientX - rect.left) / rect.width) * 700;
  const y = ((evt.clientY - rect.top) / rect.height) * 450;
  return { x: snap(x / 60), y: snap(y / 60) };
}

function draw() {
  const svg = v('floorplan'); const scale = 60; const ox = 20; const oy = 20;
  const walls = homeModel.walls.filter((w) => (w.floor_id || 'floor-ground') === selectedFloorId);
  const lights = homeModel.lights.filter((l) => (l.floor_id || 'floor-ground') === selectedFloorId);
  const doors = homeModel.doors.filter((d) => (d.floor_id || 'floor-ground') === selectedFloorId);
  const pods = homeModel.perception_pods.filter((p) => p.floor_id === selectedFloorId);
  const regions = homeModel.room_regions.filter((r) => r.floor_id === selectedFloorId);
  const rooms = homeModel.rooms.filter((r) => r.floor_id === selectedFloorId);

  let html = '<defs><pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M 30 0 L 0 0 0 30" fill="none" stroke="#1e293b" stroke-width="1"/></pattern></defs><rect x="0" y="0" width="700" height="450" fill="url(#grid)"/>';
  regions.forEach((r) => {
    const points = r.points.map((p) => `${ox + p[0] * scale},${oy + p[1] * scale}`).join(' ');
    html += `<polygon points="${points}" fill="#1d4ed833" stroke="#60a5fa" stroke-width="1.5"/><text x="${ox + r.points[0][0] * scale + 4}" y="${oy + r.points[0][1] * scale + 14}" fill="#bfdbfe">${r.name}</text>`;
  });
  rooms.forEach((r) => { html += `<rect x="${ox+r.x*scale}" y="${oy+r.y*scale}" width="${r.width*scale}" height="${r.depth*scale}" fill="none" stroke="#334155" stroke-dasharray="4 4" />`; });
  walls.forEach((w) => {
    html += `<line data-wall-id="${w.id}" x1="${ox + w.x1 * scale}" y1="${oy + w.y1 * scale}" x2="${ox + w.x2 * scale}" y2="${oy + w.y2 * scale}" stroke="#e2e8f0" stroke-width="6"/>`;
  });
  doors.forEach((d) => { html += `<rect x="${ox + d.x * scale}" y="${oy + d.y * scale}" width="${d.width * scale}" height="6" fill="#22d3ee"/>`; });
  lights.forEach((l) => { html += `<circle cx="${ox + l.x * scale}" cy="${oy + l.y * scale}" r="7" fill="#facc15"/><text x="${ox + l.x * scale + 8}" y="${oy + l.y * scale - 8}" fill="#fde68a">${l.name}</text>`; });
  pods.forEach((p) => { html += `<circle cx="${ox + p.x * scale}" cy="${oy + p.y * scale}" r="8" fill="#86efac"/><text x="${ox + p.x * scale + 8}" y="${oy + p.y * scale + 4}" fill="#bbf7d0">${p.name}</text>`; });

  if (wallStart && previewPoint) html += `<line x1="${ox + wallStart.x * scale}" y1="${oy + wallStart.y * scale}" x2="${ox + previewPoint.x * scale}" y2="${oy + previewPoint.y * scale}" stroke="#f97316" stroke-width="3" stroke-dasharray="6 4"/>`;
  if (roomPoints.length) {
    const rp = roomPoints.map((p) => `${ox + p[0] * scale},${oy + p[1] * scale}`).join(' ');
    html += `<polyline points="${rp}" fill="none" stroke="#a78bfa" stroke-width="2"/>`;
  }
  svg.innerHTML = html;
  v('mode-status').textContent = `Mode: ${mode} | ${floorName()}`;
  v('json-preview').textContent = JSON.stringify(homeModel, null, 2);
}

function finishRoom() {
  if (roomPoints.length < 3) return;
  const name = window.prompt('Room name?', `Room ${homeModel.room_regions.length + 1}`) || `Room ${homeModel.room_regions.length + 1}`;
  homeModel.room_regions.push({ id: uid('region'), floor_id: selectedFloorId, name, points: roomPoints });
  roomPoints = [];
  draw();
}

function handleSvgClick(evt) {
  const p = coordFromEvent(evt);
  if (mode === 'draw_wall') {
    if (!wallStart) wallStart = p;
    else { homeModel.walls.push({ id: uid('wall'), room_id: null, floor_id: selectedFloorId, x1: wallStart.x, y1: wallStart.y, x2: p.x, y2: p.y, thickness: 0.15 }); wallStart = null; previewPoint = null; }
  } else if (mode === 'erase_wall') {
    const wallId = evt.target?.dataset?.wallId;
    if (wallId) homeModel.walls = homeModel.walls.filter((w) => w.id !== wallId);
  } else if (mode === 'define_room') roomPoints.push([p.x, p.y]);
  else if (mode === 'place_light') homeModel.lights.push({ id: uid('light'), room_id: null, floor_id: selectedFloorId, name: `Light ${homeModel.lights.length + 1}`, x: p.x, y: p.y, type: 'ceiling' });
  else if (mode === 'place_door') homeModel.doors.push({ id: uid('door'), room_id: null, wall_id: null, floor_id: selectedFloorId, x: p.x, y: p.y, width: 0.9, swing_degrees: 90 });
  else if (mode === 'place_pod') homeModel.perception_pods.push({ id: uid('pod'), name: `Pod ${homeModel.perception_pods.length + 1}`, floor_id: selectedFloorId, x: p.x, y: p.y, orientation_degrees: 0, camera_enabled: true, microphone_enabled: true, sensors: ['camera', 'microphone'] });
  draw();
}

function initToolbar() {
  const toolbar = v('toolbar');
  const labels = { select: 'Select', draw_wall: 'Draw Wall', erase_wall: 'Erase Wall', define_room: 'Define Room', place_door: 'Place Door', place_light: 'Place Light', place_pod: 'Place Perception Pod', pan: 'Pan/Move' };
  toolbar.innerHTML = modeDefs.map((m) => `<button type="button" data-mode="${m}">${labels[m]}</button>`).join('');
  toolbar.addEventListener('click', (e) => {
    const m = e.target?.dataset?.mode; if (!m) return; mode = m; wallStart = null; previewPoint = null;
    [...toolbar.querySelectorAll('button')].forEach((b) => b.classList.toggle('active', b.dataset.mode === mode));
    draw();
  });
  toolbar.querySelector('button').classList.add('active');
}

async function refresh() { const res = await fetch('/api/home'); homeModel = await res.json(); if (!homeModel.room_regions) homeModel.room_regions = []; if (!homeModel.perception_pods) homeModel.perception_pods = []; selectedFloorId = homeModel.floors[0]?.id; fillForm(homeModel); renderFloorSelect(); draw(); }

v('home-form').addEventListener('submit', async (e) => { e.preventDefault(); mapFormToModel(homeModel); const res = await fetch('/api/home', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(homeModel) }); homeModel = await res.json(); draw(); });
v('reset-demo').addEventListener('click', async () => { const res = await fetch('/api/home/reset-demo', { method: 'POST' }); homeModel = await res.json(); selectedFloorId = homeModel.floors[0]?.id; fillForm(homeModel); renderFloorSelect(); draw(); });
v('clear-floor').addEventListener('click', () => { homeModel.walls = homeModel.walls.filter((w) => (w.floor_id || 'floor-ground') !== selectedFloorId); homeModel.doors = homeModel.doors.filter((d) => (d.floor_id || 'floor-ground') !== selectedFloorId); homeModel.lights = homeModel.lights.filter((l) => (l.floor_id || 'floor-ground') !== selectedFloorId); homeModel.room_regions = homeModel.room_regions.filter((r) => r.floor_id !== selectedFloorId); homeModel.perception_pods = homeModel.perception_pods.filter((p) => p.floor_id !== selectedFloorId); draw(); });
v('add-floor').addEventListener('click', () => { const level = homeModel.floors.length; const name = window.prompt('New floor name?', `Floor ${level}`) || `Floor ${level}`; const id = uid('floor'); homeModel.floors.push({ id, name, level }); selectedFloorId = id; renderFloorSelect(); draw(); });
v('floor-select').addEventListener('change', (e) => { selectedFloorId = e.target.value; wallStart = null; roomPoints = []; draw(); });
v('finish-room').addEventListener('click', finishRoom);
v('floorplan').addEventListener('click', handleSvgClick);
v('floorplan').addEventListener('mousemove', (evt) => { if (mode === 'draw_wall' && wallStart) { previewPoint = coordFromEvent(evt); draw(); } });
v('floorplan').addEventListener('dblclick', () => { if (mode === 'define_room') finishRoom(); });

initToolbar();
refresh();
