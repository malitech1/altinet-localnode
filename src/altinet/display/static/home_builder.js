let homeModel = null;
let lightOn = false;

function v(id) { return document.getElementById(id); }

function mapFormToModel(model) {
  model.property_name = v('property_name').value;
  model.property_boundary.width = Number(v('boundary_width').value);
  model.property_boundary.depth = Number(v('boundary_depth').value);
  model.house_dimensions.width = Number(v('house_width').value);
  model.house_dimensions.depth = Number(v('house_depth').value);
  model.rooms[0].name = v('room_name').value;
  model.rooms[0].width = Number(v('room_width').value);
  model.rooms[0].depth = Number(v('room_depth').value);
}

function fillForm(model) {
  v('property_name').value = model.property_name;
  v('boundary_width').value = model.property_boundary.width;
  v('boundary_depth').value = model.property_boundary.depth;
  v('house_width').value = model.house_dimensions.width;
  v('house_depth').value = model.house_dimensions.depth;
  v('room_name').value = model.rooms[0].name;
  v('room_width').value = model.rooms[0].width;
  v('room_depth').value = model.rooms[0].depth;
}

function draw(model) {
  const svg = v('floorplan');
  const room = model.rooms[0]; const light = model.lights[0]; const door = model.doors[0];
  const scale = 60, ox = 80, oy = 60;
  const rw = room.width * scale, rd = room.depth * scale;
  const doorX = ox + door.x * scale;
  const doorY = oy + door.y * scale;
  const lightX = ox + light.x * scale;
  const lightY = oy + light.y * scale;
  svg.innerHTML = `
    <rect x="${ox}" y="${oy}" width="${rw}" height="${rd}" fill="#1e293b" stroke="#e2e8f0" stroke-width="3" />
    <line x1="${ox}" y1="${oy}" x2="${ox+rw}" y2="${oy}" stroke="#cbd5e1" stroke-width="8" />
    <line x1="${ox+rw}" y1="${oy}" x2="${ox+rw}" y2="${oy+rd}" stroke="#cbd5e1" stroke-width="8" />
    <line x1="${ox+rw}" y1="${oy+rd}" x2="${ox}" y2="${oy+rd}" stroke="#cbd5e1" stroke-width="8" />
    <line x1="${ox}" y1="${oy+rd}" x2="${ox}" y2="${oy}" stroke="#cbd5e1" stroke-width="8" />
    <line x1="${doorX}" y1="${doorY}" x2="${doorX + (door.width*scale)}" y2="${doorY}" stroke="#0b1220" stroke-width="10" />
    <path d="M ${doorX} ${doorY} A ${door.width*scale} ${door.width*scale} 0 0 1 ${doorX} ${doorY-(door.width*scale)}" stroke="#94a3b8" fill="none" />
    <circle id="light-node" class="light ${lightOn ? 'on' : 'off'}" cx="${lightX}" cy="${lightY}" r="12" />
    <text x="${ox+10}" y="${oy+24}" fill="#e5e7eb">${room.name}</text>`;
  document.getElementById('light-node').addEventListener('click', () => {
    lightOn = !lightOn;
    console.log('Light clicked:', light.id, 'on=', lightOn);
    draw(model);
  });
  v('json-preview').textContent = JSON.stringify(model, null, 2);
}

async function refresh() {
  const res = await fetch('/api/home');
  homeModel = await res.json();
  fillForm(homeModel);
  draw(homeModel);
}

v('home-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  mapFormToModel(homeModel);
  const res = await fetch('/api/home', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(homeModel) });
  homeModel = await res.json();
  draw(homeModel);
});

v('reset-demo').addEventListener('click', async () => {
  const res = await fetch('/api/home/reset-demo', { method: 'POST' });
  homeModel = await res.json();
  fillForm(homeModel);
  draw(homeModel);
});

refresh();
