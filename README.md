# altinet-localnode

A prototype of **Altinet LocalNode**, a local home-intelligence CLI for contextualising house state, simulating events, running decision engines, and testing perception/memory/runtime workflows.

## What you can run

The CLI entrypoint is implemented in `src/altinet/main.py` and exposes these commands:

- `contextualise`
- `build-prompt`
- `decide` (`--engine mock_engine` or `--engine openai`)
- `webcam-test`
- `capture-room`
- `observe-room`
- `analyse-room-image`
- `simulate-events`
- `memory-demo`
- `runtime`

Running the CLI with no command prints:

```text
Altinet LocalNode running
```

---

## Prerequisites

- **Windows 10/11**
- **Python 3.11+** (64-bit)
- **PyCharm** (Community or Professional)
- Optional hardware: a webcam for `capture-room`
- Optional API access: an OpenAI API key for OpenAI-powered commands

---

## PyCharm setup (Windows)

1. **Clone the repository**
   ```powershell
   git clone <your-repo-url>
   cd altinet-localnode
   ```

2. **Open in PyCharm**
   - PyCharm → **Open** → select the cloned `altinet-localnode` folder.

3. **Configure the project interpreter (virtual environment)**
   - PyCharm → **File** → **Settings** → **Project: altinet-localnode** → **Python Interpreter**.
   - Click the gear icon → **Add...**
   - Choose **Virtualenv Environment**.
   - Base interpreter: Python 3.11+
   - Location: `.venv` in this project
   - Click **OK**.

4. **Open PyCharm Terminal**
   - View → Tool Windows → **Terminal**.
   - Confirm Python points to your `.venv`:
     ```powershell
     python --version
     ```

---

## Local environment setup (terminal)

From the project root:

1. **Create virtual environment**
   ```powershell
   py -3.11 -m venv .venv
   ```

2. **Activate virtual environment**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Install package in editable mode**
   ```powershell
   pip install -e .
   ```

Editable install is recommended so `python -m altinet.main ...` works reliably from terminal and PyCharm run configurations.

---

## OpenAI key setup (only for OpenAI commands)

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_VISION_MODEL=gpt-4.1-mini
```

The following commands require `OPENAI_API_KEY`:
- `decide ... --engine openai`
- `analyse-room-image ...`

Other commands work without an OpenAI key.

---


### Webcam perception quickstart (PyCharm / Windows)

1. Ensure a webcam is connected and not being used by another app (Zoom/Teams/Camera).
2. In PyCharm terminal, run:
   ```powershell
   python -m altinet.main webcam-test
   ```
3. Capture one frame:
   ```powershell
   python -m altinet.main capture-room
   ```
4. Run local room observation (no OpenAI call):
   ```powershell
   python -m altinet.main observe-room
   ```

Captured images are saved under `data/captures/`:
- `data/captures/latest.jpg` (always overwritten on each capture)
- optional timestamped files can be enabled in code (`capture_single_frame(..., save_timestamped=True)`)

Troubleshooting webcam permissions (Windows):
- Settings → Privacy & security → Camera → enable camera access and app access.
- Close other apps using the webcam before running Altinet commands.
- In PyCharm, restart the run configuration/interpreter after granting permissions.

## Dashboard access

- Open the main dashboard at `/`.
- Access Home Builder from the left sidebar (**Home Builder**) or the **Edit Home / Floorplan** button on the dashboard.
- Home Builder URL: `/home-builder`.

## Floorplan Editor controls

- **Select object**: choose **Select** mode, then click walls, rooms, doors, windows, lights, or perception pods.
- **Edit object properties**: after selecting an object, use the **Selected ...** panel and click **Apply Changes**.
- **Delete object**:
  - Use **Erase** mode and click an object, or
  - Select an object in **Select** mode and click **Delete Selected**.
- **Define Room / Finish Room / Cancel Room**:
  - Use **Define Room** mode and click at least 3 points to draft a room.
  - Click **Finish Room** to save the room polygon.
  - Click **Cancel Room** to discard only the unfinished room draft.
- **Escape key**: when room drafting is active, press **Escape** to cancel unfinished room points.

---

## Dashboard floorplan note

The current dashboard floorplan is a **mock visual layer** rendered in CSS/JavaScript for UI prototyping. It displays room tiles and overlays residents/devices/agents from `/api/state` when available, with placeholders when runtime files are missing. Real editable floorplan JSON integration is planned for a later phase.

---


## AHLAN OpenAI chat setup

1. Copy `.env.example` to `.env` and set:
   - `OPENAI_API_KEY=your_api_key_here`
   - `AHLAN_MODEL=gpt-5.5-mini` (or another supported model)
2. Run dashboard:
   - `python -m altinet.main dashboard --host 127.0.0.1 --port 8000`
3. Open `http://127.0.0.1:8000` and use the AHLAN Assistant card.
4. Test assistant chat API:
   - `pytest tests/test_users_and_assistant.py tests/test_display_dashboard.py`

Privacy note: user profile context is sent to OpenAI only when OpenAI-powered AHLAN chat is enabled with `OPENAI_API_KEY`. Without a key, chat uses local fallback responses.

## Running tests

From project root (with `.venv` active):

```powershell
pytest
```

---

## Running the demos

Use these commands from the repository root. All examples below assume your virtual environment is active and package is installed editable.

### 0) Basic CLI run

```powershell
python -m altinet.main
```

Expected behavior:
- Prints: `Altinet LocalNode running`

---

### 1) Contextualise

```powershell
python -m altinet.main contextualise --sample-path examples/sample_house_state.json
```

Optional events:

```powershell
python -m altinet.main contextualise --sample-path examples/sample_house_state.json --event "Motion detected in hallway" --event "Front door opened"
```

Expected behavior:
- Prints a natural-language summary of house state (time, occupants, room context, etc.).

Uses:
- `examples/sample_house_state.json`

---

### 2) Build prompt

```powershell
python -m altinet.main build-prompt examples/sample_house_state.json
```

Optional events:

```powershell
python -m altinet.main build-prompt examples/sample_house_state.json --event "Elliot entered bedroom" --event "Lights are off"
```

Expected behavior:
- Prints the full decision prompt including system role, context block, action set, and required JSON response format.

Uses:
- `examples/sample_house_state.json`

---

### 3) Decide (mock engine)

```powershell
python -m altinet.main decide examples/sample_house_state.json --engine mock_engine
```

(`--engine mock_engine` is optional; it is the default.)

Expected behavior:
- Prints JSON decision output from local mock logic (for example selected action and confidence).
- No API key required.

Uses:
- `examples/sample_house_state.json`

---

### 4) Decide (OpenAI engine)

```powershell
python -m altinet.main decide examples/sample_house_state.json --engine openai
```

Expected behavior:
- Builds prompt from house state, sends to OpenAI, validates response, prints JSON decision.
- If key/model/config is missing, prints a `Decision error: ...` message.

Requires:
- `OPENAI_API_KEY`
- Optional: `OPENAI_VISION_MODEL` (defaults to `gpt-4.1-mini`)

Uses:
- `examples/sample_house_state.json`

---

### 5) Capture room (webcam)

```powershell
python -m altinet.main capture-room
```

Expected behavior:
- Tries to capture one frame from the default webcam.
- On success: saves image to `data/captures/latest.jpg` and prints `Capture complete: ...`
- On failure (no camera/busy camera): prints `Capture skipped: ...`

Requires:
- Webcam access

Creates/uses:
- `data/captures/latest.jpg` (created at runtime)

---

### 6) Analyse room image (OpenAI Vision)

If you already ran `capture-room`:

```powershell
python -m altinet.main analyse-room-image data/captures/latest.jpg
```

Or provide any local image path:

```powershell
python -m altinet.main analyse-room-image <path-to-image>
```

Expected behavior:
- Sends image to OpenAI Vision for structured room-context extraction.

Privacy note:
- Images are processed locally by default.
- A captured image is only sent to OpenAI when you explicitly run `analyse-room-image`.
- `observe-room` remains local-only and does not upload image data.

Expected output schema:
```json
{
  "room_type_guess": "bedroom | kitchen | living_room | office | bathroom | unknown",
  "visible_people": [],
  "visible_pets": [],
  "visible_devices": [],
  "lights_on": true,
  "lighting_description": "...",
  "notable_objects": [],
  "safety_concerns": [],
  "summary": "..."
}
```
- Saves validated JSON to `data/context/latest_room_context.json`.
- Prints the saved JSON.
- If OpenAI call/config fails, prints `Room context error: ...`.

Requires:
- `OPENAI_API_KEY`
- Optional: `OPENAI_VISION_MODEL` (defaults to `gpt-4.1-mini`)

Uses/creates:
- Input image path you provide
- `data/context/latest_room_context.json` (created at runtime)

---

### 7) Simulate events

```powershell
python -m altinet.main simulate-events
```

Expected behavior:
- Simulates events (e.g., resident entering bedroom at 8:00 PM).
- Processes queue + context update.
- Prints updated context and a mock decision JSON.

Uses:
- `examples/sample_house_state.json`

---

### 8) Memory demo

```powershell
python -m altinet.main memory-demo
```

Expected behavior:
- Seeds sample episodic memories.
- Retrieves and prints ranked relevant memories for a sample context.

---

### 9) Runtime loop

Basic bounded run:

```powershell
python -m altinet.main runtime --sample-path examples/sample_house_state.json --tick-rate 1.0 --max-ticks 5
```

Expected behavior:
- Runs the runtime loop.
- Stops after max ticks (if provided).
- Prints summary like: `Runtime stopped after X ticks; events=...; decisions=...; errors=...`

Uses:
- `examples/sample_house_state.json`

---

## Demo requirements at a glance

- **Needs `OPENAI_API_KEY`**:
  - `decide ... --engine openai`
  - `analyse-room-image ...`

- **Needs webcam**:
  - `webcam-test`
- `capture-room`
- `observe-room`

- **No OpenAI/webcam required**:
  - basic CLI run
  - `contextualise`
  - `build-prompt`
  - `decide ... --engine mock_engine`
  - `simulate-events`
  - `memory-demo`
  - `runtime`

---

## Troubleshooting (Windows + PyCharm)

### `ModuleNotFoundError: No module named 'altinet'`

Fix:
1. Ensure virtualenv is active.
2. Run editable install again:
   ```powershell
   pip install -e .
   ```
3. In PyCharm, confirm the selected interpreter is the project `.venv`.

### `python` or `py` points to wrong version

Fix:
- Verify versions:
  ```powershell
  py -0p
  python --version
  ```
- Recreate `.venv` with Python 3.11+ and reselect interpreter in PyCharm.

### `OPENAI_API_KEY` not found / OpenAI command fails

Fix:
1. Ensure `.env` exists in project root.
2. Ensure key name is exactly `OPENAI_API_KEY`.
3. Restart PyCharm terminal/run config after editing `.env`.

### Webcam errors (`capture-room` skipped)

Common causes:
- Camera in use by Zoom/Teams/Browser
- Windows privacy camera permission denied
- External camera not initialized

Fix:
1. Close other apps using camera.
2. Windows Settings → Privacy & security → Camera → allow desktop app access.
3. Retry command.

### `opencv-python` install/import issues

Fix:
```powershell
python -m pip install --upgrade pip
pip install --force-reinstall opencv-python
```

### PyCharm test discovery issues

Fix:
1. Set **Default test runner** to `pytest` (Settings → Tools → Python Integrated Tools).
2. Run tests from project root.
3. Ensure interpreter is `.venv` and dependencies are installed.

---

## Dashboard (LocalNode display panel)

Run the FastAPI dashboard:

```powershell
python -m altinet.main dashboard
```

Open in browser:

- `http://127.0.0.1:8000`

The page auto-refreshes every 2 seconds by polling `GET /api/state`.

### Recommended workflow with webcam capture

1. Capture latest image:
   ```powershell
   python -m altinet.main capture-room
   ```
2. Refresh browser (or wait for auto-refresh).
3. Optional: run runtime loop in another terminal so `data/runtime/runtime_state.json` updates continuously.

### PyCharm / Windows port troubleshooting

If port `8000` is already used in PyCharm or Windows:

```powershell
python -m altinet.main dashboard --port 8010
```

Then open `http://127.0.0.1:8010`.

If binding fails:
- Close any existing Python/Uvicorn process using the same port.
- In PyCharm, stop old run configurations before starting a new dashboard run.
- Use `--host 127.0.0.1` explicitly if firewall/network policy blocks non-local binding.

## Home Builder (first module)

The Home Builder now starts in a **blank project mode** for development workflows.

Run the dashboard server:

```powershell
uvicorn altinet.display.app:create_app --reload
```

Open:

- `http://127.0.0.1:8000/home-builder`

How to use:

- Start from **New Altinet Home** (blank): one empty ground floor, no default walls/rooms/doors/windows/lights/pods.
- Use **Load Demo** anytime to load the sample prebuilt home.
- Grid units are in **metres** in the JSON model.
- Scale: **1 grid square = 0.5 m** (shown on the editor canvas).
- Draw walls in **Draw Wall** mode (choose internal/external wall type).
- Define rooms in **Define Room** mode with live preview: each click adds visible point markers, temporary edges, and translucent area fill (after 3+ points), then click **Finish Room** to name/type and save the room polygon.
- Use **Clear Room Draft** to cancel unfinished room polygons.
- Place doors/windows in **Place Door** / **Place Window** mode; they snap to nearby walls and store `wall_id` + `position_along_wall_m`.
- **Place Light** adds a visible light marker immediately at the clicked SVG coordinate and stores metre-based `x/y` coordinates in the HomeModel.
- **Place Perception Pod** adds a visible pod marker immediately at the clicked SVG coordinate and stores `x/y`, `orientation_degrees`, `camera_enabled`, and `microphone_enabled`.
- Click handling is mode-specific: **Select**, **Draw Wall**, **Erase**, **Define Room**, **Place Door**, **Place Window**, **Place Light**, **Place Perception Pod**, and **Pan** each route clicks through the same SVG coordinate helper (`getSvgPoint`).
- Status/debug line now shows current mode, last click coordinates, and last action taken to help verify editor interactions quickly.
- Select mode is the single edit/inspect mode: click wall/room/door/window/light/perception pod to highlight and open the properties panel; click empty background to clear selection.
- Door/window properties panel supports in-place editing (`position_along_wall_m`, `width_m`, `height_m` for windows, `swing_direction` for doors, optional name) with **Apply Changes**, **Delete Selected**, and **Close**.
- Zoom controls (**Zoom In**, **Zoom Out**, **Reset Zoom**) change the SVG `viewBox` and show live zoom percentage.
- Grid and ruler labels are zoom-aware and switch scale from metres to centimetres.

Manual verification checklist:

1. Select a door, change `width_m`, click **Apply Changes**, and confirm the rendered opening width + JSON preview update immediately.
2. Select a window, change `width_m` and `height_m`, click **Apply Changes**, and confirm immediate visual + JSON update.
3. Use **Zoom In/Out/Reset** and verify zoom percentage updates while floorplan objects remain selectable.
4. Confirm grid scale label/ruler transitions across zoom levels (for example `Grid: 1 m`, `Grid: 50 cm`, `Grid: 10 cm`, `Grid: 1 cm`).
5. While zoomed in/out, place walls/doors/windows/lights/pods and verify placement/snapping coordinates remain accurate.

Regression checklist for current editor reliability fixes:

- [ ] Zoom In changes grid scale.
- [ ] Zoom Out changes grid scale.
- [ ] Reset Zoom restores full plan.
- [ ] Select wall shows wall properties.
- [ ] Select door shows door properties.
- [ ] Select window shows window properties.
- [ ] Select light shows light properties.
- [ ] Select perception pod shows pod properties.
- [ ] Duplicate light placement is rejected.
- [ ] Overlapping door/window placement is rejected.

## User Profiles

The dashboard now supports resident/user profile management via `/api/users`.

- Stored at `data/users/user_profiles.json`.
- Profile fields include role, access level, preferred name, optional notes/pronouns, and placeholders for preferences/routines.
- CRUD API:
  - `GET /api/users`
  - `POST /api/users`
  - `POST /api/users/seed-demo`
  - `GET /api/users/{user_id}`
  - `PATCH /api/users/{user_id}`
  - `DELETE /api/users/{user_id}`

## AHLAN Assistant

The dashboard includes an **AHLAN Assistant** card with:

- local chat history panel,
- message input,
- send button,
- greeting:
  `Hello, I’m AHLAN. I can help manage the home and learn resident preferences.`

## Troubleshooting blank dashboard/loading states

If the dashboard appears blank or cards remain on `Loading...`:

1. Open browser developer tools and check the console/network for failures on:
   - `GET /api/state`
   - `GET /api/users`
   - `POST /api/assistant/chat`
   - static assets under `/static/*`
2. Run tests:
   - `pytest tests/test_display_dashboard.py tests/test_users_and_assistant.py tests/test_assistant_openai_chat.py`
3. Confirm API responses are valid JSON:
   - `curl -s http://127.0.0.1:8000/api/state | jq`
   - `curl -s http://127.0.0.1:8000/api/users | jq`

The dashboard now renders resilient fallback/demo content when runtime/context/user files are missing.

## Future direction

Planned next steps include OpenAI-powered conversation, preference extraction, and user-approved profile learning.

## LocalNode Backend Store

- JSON backend files are in `data/altinet/`:
  - `users/users.json`
  - `home/home.json`
  - `agents/agents.json`
  - `devices/devices.json`
  - `context/user_context.json`
  - `context/house_context.json`
- Seed demo data with:
  - `python -m altinet.main seed-demo-data`
- Access levels include resident, guest, service, dependent, animal, unknown, and threat-oriented levels (including `intruder`).
- Dashboard state now includes a registry snapshot from `/api/registry`, and `/api/state` exposes registry users for display consumption.


### Dashboard users from LocalNode registry

1. Run the dashboard:
   - `uvicorn altinet.display.app:create_app --reload`
2. Open `http://127.0.0.1:8000`.
3. In **Residents / Users**, click **Seed Demo Users**.
4. Demo users should appear in the Residents / Users card immediately.
5. User profiles are stored in `data/altinet/users/users.json`.
