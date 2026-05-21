from altinet.main import main


def test_main_prints_running_message(capsys):
    main([])
    captured = capsys.readouterr()
    assert "Altinet LocalNode running" in captured.out


def test_contextualise_command_prints_context_block(capsys):
    main(["contextualise", "--sample-path", "examples/sample_house_state.json"])
    captured = capsys.readouterr()

    assert "The current time is 8:00 PM." in captured.out
    assert "Elliot is in the bedroom." in captured.out


def test_build_prompt_command_prints_complete_prompt(capsys):
    main(["build-prompt", "examples/sample_house_state.json"])
    captured = capsys.readouterr()

    assert "# System Role" in captured.out
    assert "# Required JSON Response Format" in captured.out
    assert "turn_light_on" in captured.out


def test_decide_command_prints_mock_decision(capsys):
    main(["decide", "examples/sample_house_state.json"])
    captured = capsys.readouterr()

    assert '"selected_action": "turn_light_on"' in captured.out
    assert '"confidence"' in captured.out


def test_decide_command_accepts_openai_engine_flag(monkeypatch, capsys):
    from altinet.context.schemas import DecisionResponse

    def _fake_decide(_prompt):
        return DecisionResponse(selected_action="do_nothing", rationale="safe default")

    monkeypatch.setattr("altinet.main.decide_action_with_openai", _fake_decide)
    main(["decide", "examples/sample_house_state.json", "--engine", "openai"])
    captured = capsys.readouterr()

    assert '"selected_action": "do_nothing"' in captured.out
    assert '"rationale": "safe default"' in captured.out


def test_capture_room_command_reports_success(monkeypatch, capsys):
    monkeypatch.setattr("altinet.main.capture_room_image", lambda: (True, "Captured image saved to data/captures/latest.jpg"))

    main(["capture-room"])
    captured = capsys.readouterr()

    assert "Capture complete:" in captured.out
    assert "data/captures/latest.jpg" in captured.out


def test_capture_room_command_reports_missing_camera(monkeypatch, capsys):
    monkeypatch.setattr("altinet.main.capture_room_image", lambda: (False, "No camera detected or camera is unavailable."))

    main(["capture-room"])
    captured = capsys.readouterr()

    assert "Capture skipped:" in captured.out
    assert "No camera detected" in captured.out


def test_analyse_room_image_command_saves_context(monkeypatch, tmp_path, capsys):
    from altinet.context.schemas import RoomContextResponse

    image_path = tmp_path / "latest.jpg"
    image_path.write_bytes(b"fake")

    monkeypatch.setattr(
        "altinet.main.analyse_room_image_with_openai",
        lambda _path: RoomContextResponse(
            room_type_guess="bedroom",
            visible_people=["adult"],
            visible_pets=[],
            lights_on=True,
            notable_objects=["bed", "lamp"],
            safety_concerns=[],
            summary="A tidy bedroom with one visible adult.",
        ),
    )
    monkeypatch.setattr("altinet.main.DEFAULT_ROOM_CONTEXT_OUTPUT_PATH", tmp_path / "latest_room_context.json")

    main(["analyse-room-image", str(image_path)])
    captured = capsys.readouterr()

    assert "Room context saved to" in captured.out
    out_file = tmp_path / "latest_room_context.json"
    assert out_file.exists()
    assert '"room_type_guess": "bedroom"' in out_file.read_text(encoding="utf-8")


def test_simulate_events_command_prints_decision(capsys):
    main(["simulate-events"])
    captured = capsys.readouterr()

    assert "Simulated event: Elliot enters bedroom at 8:00 PM" in captured.out
    assert "Mock decision:" in captured.out
    assert '"selected_action": "turn_light_on"' in captured.out


def test_memory_demo_command_prints_ranked_memories(capsys):
    main(["memory-demo"])
    captured = capsys.readouterr()

    assert "Memory demo: relevant episodic memories" in captured.out
    assert "1. Elliot read a bedtime story to Mia." in captured.out


def test_runtime_command_runs_loop(monkeypatch, capsys):
    from altinet.runtime.runtime_loop import RuntimeStats

    monkeypatch.setattr(
        "altinet.main.run_runtime_loop",
        lambda *_args, **_kwargs: RuntimeStats(ticks=3, events_processed=6, decisions_made=3, loop_errors=0),
    )

    main(["runtime", "--max-ticks", "3"])
    captured = capsys.readouterr()

    assert "Runtime stopped after 3 ticks" in captured.out
    assert "events=6" in captured.out


def test_webcam_test_command_reports_status(monkeypatch, capsys):
    monkeypatch.setattr("altinet.main.capture_room_image", lambda: (True, "Captured image saved to data/captures/latest.jpg"))

    main(["webcam-test"])
    captured = capsys.readouterr()

    assert "Webcam OK:" in captured.out


def test_observe_room_command_prints_structured_output(monkeypatch, capsys):
    from altinet.perception.models import CameraFrame, LightingObservation, PerceptionObservation, RoomObservation
    from datetime import datetime, timezone
    from pathlib import Path

    ts = datetime.now(timezone.utc)
    fake = PerceptionObservation(
        frame=CameraFrame(image_path=Path("data/captures/latest.jpg"), captured_at=ts, camera_available=True),
        room=RoomObservation(
            image_path=Path("data/captures/latest.jpg"),
            timestamp=ts,
            camera_available=True,
            lighting=LightingObservation(brightness_estimate=123, lighting_guess="dim"),
        ),
    )
    monkeypatch.setattr("altinet.main.observe_room", lambda: fake)

    main(["observe-room"])
    captured = capsys.readouterr()

    assert '"source": "webcam"' in captured.out
    assert '"lighting_guess": "dim"' in captured.out
