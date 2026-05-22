function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

async function loadHomeLocation() {
  const res = await fetch('/api/home/location');
  const loc = await res.json();
  const fields = ['address_line_1', 'address_line_2', 'suburb_city', 'state_region', 'postcode', 'country'];
  fields.forEach((f) => {
    const el = document.querySelector(`[name="${f}"]`);
    if (el) el.value = loc[f] || '';
  });
  setText('location-status', `Verification: ${loc.address_verified ? 'Verified' : 'Not verified'}`);
  setText('formatted-address', loc.formatted_address ? `Formatted: ${loc.formatted_address}` : '');
  setText('lat-lon', (loc.latitude !== null && loc.longitude !== null) ? `Lat/Lon: ${loc.latitude}, ${loc.longitude}` : '');
}

async function saveHomeLocation(event) {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.target).entries());
  const res = await fetch('/api/home/location', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (!res.ok) {
    setText('location-status', 'Verification: save failed');
    return;
  }
  await loadHomeLocation();
}

async function verifyHomeLocation() {
  const res = await fetch('/api/home/location/verify', { method: 'POST' });
  const payload = await res.json();
  setText('location-status', `Verification: ${payload.success ? 'Verified' : 'Not verified'}${payload.message ? ` (${payload.message})` : ''}`);
  await loadHomeLocation();
}

async function loadSettings() {
  const res = await fetch('/api/settings');
  const settings = await res.json();
  setText('settings-openai', `Configured: ${settings.openai.configured ? 'Yes' : 'No'} · Model: ${settings.openai.model || 'N/A'}`);
  setText('settings-weather', `Provider: ${settings.weather.provider || 'unknown'} · Google Maps configured: ${settings.google_maps.configured ? 'Yes' : 'No'}`);
  setText('settings-perception', `Default camera index: ${settings.perception.default_camera_index} · Save timestamped captures: ${settings.perception.save_timestamped_captures}`);
  setText('settings-runtime', `Tick rate (Hz): ${settings.runtime.tick_rate_hz}`);
  setText('settings-data', `Data directory: ${settings.data.data_dir}`);
  setText('settings-integrations', `Google Maps configured: ${settings.google_maps.configured ? 'Yes' : 'No'} · More integrations coming soon.`);
}

document.addEventListener('DOMContentLoaded', async () => {
  document.getElementById('home-location-form')?.addEventListener('submit', saveHomeLocation);
  document.getElementById('verify-address-button')?.addEventListener('click', verifyHomeLocation);
  await loadHomeLocation();
  await loadSettings();
});
