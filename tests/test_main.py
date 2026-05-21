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
