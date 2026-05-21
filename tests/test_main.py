from altinet.main import main


def test_main_prints_running_message(capsys):
    main()
    captured = capsys.readouterr()
    assert "Altinet LocalNode running" in captured.out
