let homeModel = null;
const modeDefs = ["select", "draw_wall", "erase_wall", "define_room", "place_door", "place_light", "place_pod", "pan"];
let mode = "select";
let selectedFloorId = null;
let wallStart = null;
let previewPoint = null;
let roomPoints = [];
let selectedObject = null;

function v(id) { return document.getElementById(id); }
function uid(prefix) { return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 1000)}`; }
function snap(n) { return Math.round(n * 2) / 2; }
function floorRef(id) { return id || 'floor-ground'; }
function getSvgPoint(evt) {
  const svg = v('floorplan');
  const point = svg.createSVGPoint();
  point.x = evt.clientX;
  point.y = evt.clientY;
  const ctm = svg.getScreenCTM();
  if (!ctm) return { x: 0, y: 0 };
  const p = point.matrixTransform(ctm.inverse());
  return { x: snap((p.x - 20) / 60), y: snap((p.y - 20) / 60) };
}
function deleteObject(type, id) {
  const map = { wall: 'walls', room_region: 'room_regions', door: 'doors', light: 'lights', pod: 'perception_pods' };
  const key = map[type]; if (!key) return;
  homeModel[key] = homeModel[key].filter((o) => o.id !== id);
  if (selectedObject && selectedObject.id === id && selectedObject.type === type) selectedObject = null;
}
function renderSelectionPanel() {
  const p = v('selection-panel');
  if (!selectedObject) { p.textContent = 'No object selected.'; return; }
  const extra = selectedObject.type === 'wall' ? `<div>wall_type: ${selectedObject.wall_type || 'internal'}</div>` : '';
  p.innerHTML = `<div><strong>Selected</strong></div><div>type: ${selectedObject.type}</div><div>id: ${selectedObject.id}</div>${extra}`;
}
function draw() {
  const svg = v('floorplan'); const scale = 60; const ox = 20; const oy = 20;
  const walls = homeModel.walls.filter((w) => floorRef(w.floor_id) === selectedFloorId);
  const lights = homeModel.lights.filter((l) => floorRef(l.floor_id) === selectedFloorId);
  const doors = homeModel.doors.filter((d) => floorRef(d.floor_id) === selectedFloorId);
  const pods = homeModel.perception_pods.filter((p) => p.floor_id === selectedFloorId);
  const regions = homeModel.room_regions.filter((r) => r.floor_id === selectedFloorId);
  const rooms = homeModel.rooms.filter((r) => r.floor_id === selectedFloorId);

  let html = '<defs><pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M 30 0 L 0 0 0 30" fill="none" stroke="#1e293b" stroke-width="1"/></pattern></defs><rect x="0" y="0" width="700" height="450" fill="url(#grid)"/>';
  regions.forEach((r) => { const points = r.points.map((p) => `${ox + p[0] * scale},${oy + p[1] * scale}`).join(' '); html += `<polygon data-type="room_region" data-id="${r.id}" points="${points}" fill="#1d4ed822" stroke="#60a5fa" stroke-width="1.5"/>`; });
  rooms.forEach((r) => { html += `<rect x="${ox+r.x*scale}" y="${oy+r.y*scale}" width="${r.width*scale}" height="${r.depth*scale}" fill="none" stroke="#334155" stroke-dasharray="4 4" />`; });
  walls.forEach((w) => {
    const external = (w.wall_type || 'internal') === 'external';
    const selected = selectedObject?.type === 'wall' && selectedObject.id === w.id;
    html += `<line data-type="wall" data-id="${w.id}" x1="${ox + w.x1 * scale}" y1="${oy + w.y1 * scale}" x2="${ox + w.x2 * scale}" y2="${oy + w.y2 * scale}" stroke="${selected ? '#f43f5e' : (external ? '#f8fafc' : '#94a3b8')}" stroke-width="${external ? 8 : 5}"/>`;
  });
  doors.forEach((d) => { html += `<rect data-type="door" data-id="${d.id}" x="${ox + d.x * scale}" y="${oy + d.y * scale}" width="${d.width * scale}" height="6" fill="#22d3ee"/>`; });
  lights.forEach((l) => { html += `<circle data-type="light" data-id="${l.id}" cx="${ox + l.x * scale}" cy="${oy + l.y * scale}" r="7" fill="#facc15"/>`; });
  pods.forEach((p) => { html += `<circle data-type="pod" data-id="${p.id}" cx="${ox + p.x * scale}" cy="${oy + p.y * scale}" r="8" fill="#86efac"/>`; });
  if (wallStart && previewPoint) html += `<line x1="${ox + wallStart.x * scale}" y1="${oy + wallStart.y * scale}" x2="${ox + previewPoint.x * scale}" y2="${oy + previewPoint.y * scale}" stroke="#f97316" stroke-width="3" stroke-dasharray="6 4"/>`;
  if (roomPoints.length) html += `<polyline points="${roomPoints.map((p) => `${ox + p[0] * scale},${oy + p[1] * scale}`).join(' ')}" fill="none" stroke="#a78bfa" stroke-width="2"/>`;
  svg.innerHTML = html;
  v('wall-type-select').style.display = mode === 'draw_wall' ? 'inline-block' : 'none';
  v('mode-status').textContent = `Mode: ${mode}`;
  v('json-preview').textContent = JSON.stringify(homeModel, null, 2);
  renderSelectionPanel();
}
function handleSvgClick(evt) {
  const type = evt.target?.dataset?.type; const id = evt.target?.dataset?.id;
  if (mode === 'erase_wall' && type && id) { deleteObject(type, id); draw(); return; }
  if (mode === 'select') { selectedObject = type && id ? (homeModel.walls.concat(homeModel.room_regions, homeModel.doors, homeModel.lights, homeModel.perception_pods).find((o) => o.id === id) ? { ...homeModel.walls.concat(homeModel.room_regions, homeModel.doors, homeModel.lights, homeModel.perception_pods).find((o) => o.id === id), type } : null) : null; draw(); return; }
  const p = getSvgPoint(evt);
  if (mode === 'draw_wall') {
    if (!wallStart) wallStart = p;
    else { homeModel.walls.push({ id: uid('wall'), room_id: null, floor_id: selectedFloorId, x1: wallStart.x, y1: wallStart.y, x2: p.x, y2: p.y, thickness: 0.15, wall_type: v('wall-type-select').value }); wallStart = null; previewPoint = null; }
  } else if (mode === 'define_room') roomPoints.push([p.x, p.y]);
  else if (mode === 'place_light') homeModel.lights.push({ id: uid('light'), room_id: null, floor_id: selectedFloorId, name: `Light ${homeModel.lights.length + 1}`, x: p.x, y: p.y, type: 'ceiling' });
  else if (mode === 'place_door') homeModel.doors.push({ id: uid('door'), room_id: null, wall_id: null, floor_id: selectedFloorId, x: p.x, y: p.y, width: 0.9, swing_degrees: 90 });
  else if (mode === 'place_pod') homeModel.perception_pods.push({ id: uid('pod'), name: `Pod ${homeModel.perception_pods.length + 1}`, floor_id: selectedFloorId, x: p.x, y: p.y, orientation_degrees: 0, camera_enabled: true, microphone_enabled: true, sensors: ['camera', 'microphone'] });
  draw();
}
function finishRoom() { if (roomPoints.length < 3) return; homeModel.room_regions.push({ id: uid('region'), floor_id: selectedFloorId, name: `Room ${homeModel.room_regions.length + 1}`, points: roomPoints }); roomPoints = []; draw(); }
function initToolbar() { const toolbar = v('toolbar'); const labels = { select: 'Select', draw_wall: 'Draw Wall', erase_wall: 'Erase', define_room: 'Define Room', place_door: 'Place Door', place_light: 'Place Light', place_pod: 'Place Perception Pod', pan: 'Pan/Move' }; toolbar.innerHTML = modeDefs.map((m) => `<button type="button" data-mode="${m}">${labels[m]}</button>`).join(''); toolbar.addEventListener('click', (e) => { const m = e.target?.dataset?.mode; if (!m) return; mode = m; wallStart = null; previewPoint = null; [...toolbar.querySelectorAll('button')].forEach((b) => b.classList.toggle('active', b.dataset.mode === mode)); draw(); }); toolbar.querySelector('button').classList.add('active'); }
async function refresh() { const res = await fetch('/api/home'); homeModel = await res.json(); if (!homeModel.room_regions) homeModel.room_regions = []; if (!homeModel.perception_pods) homeModel.perception_pods = []; selectedFloorId = homeModel.floors[0]?.id; Object.values(homeModel.walls).forEach((w) => { if (!w.wall_type) w.wall_type = 'internal'; }); fillForm(homeModel); renderFloorSelect(); draw(); }
function mapFormToModel(model) { model.property_name = v('property_name').value; model.property_boundary.width = Number(v('boundary_width').value); model.property_boundary.depth = Number(v('boundary_depth').value); model.house_dimensions.width = Number(v('house_width').value); model.house_dimensions.depth = Number(v('house_depth').value); }
function fillForm(model) { v('property_name').value = model.property_name; v('boundary_width').value = model.property_boundary.width; v('boundary_depth').value = model.property_boundary.depth; v('house_width').value = model.house_dimensions.width; v('house_depth').value = model.house_dimensions.depth; }
function renderFloorSelect() { const select = v('floor-select'); select.innerHTML = homeModel.floors.map((f) => `<option value="${f.id}">${f.name}</option>`).join(''); select.value = selectedFloorId; }
v('home-form').addEventListener('submit', async (e) => { e.preventDefault(); mapFormToModel(homeModel); const res = await fetch('/api/home', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(homeModel) }); homeModel = await res.json(); draw(); });
v('clear-floor').addEventListener('click', () => { if (!window.confirm('Clear all objects on selected floor?')) return; homeModel.walls = homeModel.walls.filter((w) => floorRef(w.floor_id) !== selectedFloorId); homeModel.doors = homeModel.doors.filter((d) => floorRef(d.floor_id) !== selectedFloorId); homeModel.lights = homeModel.lights.filter((l) => floorRef(l.floor_id) !== selectedFloorId); homeModel.room_regions = homeModel.room_regions.filter((r) => r.floor_id !== selectedFloorId); homeModel.perception_pods = homeModel.perception_pods.filter((p) => p.floor_id !== selectedFloorId); selectedObject = null; draw(); });
v('delete-floor').addEventListener('click', () => { if (homeModel.floors.length <= 1) { window.alert('Cannot delete the final floor.'); return; } if (!window.confirm('Delete selected floor and all its objects?')) return; homeModel.floors = homeModel.floors.filter((f) => f.id !== selectedFloorId); v('clear-floor').click(); selectedFloorId = homeModel.floors[0].id; renderFloorSelect(); draw(); });
v('delete-selected').addEventListener('click', () => { if (!selectedObject) return; deleteObject(selectedObject.type, selectedObject.id); draw(); });
v('add-floor').addEventListener('click', () => { const level = homeModel.floors.length; const id = uid('floor'); homeModel.floors.push({ id, name: `Floor ${level}`, level }); selectedFloorId = id; renderFloorSelect(); draw(); });
v('floor-select').addEventListener('change', (e) => { selectedFloorId = e.target.value; wallStart = null; roomPoints = []; selectedObject = null; draw(); });
v('finish-room').addEventListener('click', finishRoom);
v('floorplan').addEventListener('click', handleSvgClick);
v('floorplan').addEventListener('mousemove', (evt) => { if (mode === 'draw_wall' && wallStart) { previewPoint = getSvgPoint(evt); draw(); } });
initToolbar(); refresh();
