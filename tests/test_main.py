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
