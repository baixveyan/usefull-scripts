from wows_assistant.cli import build_parser


def test_doctor_command_parses() -> None:
    args = build_parser().parse_args(["doctor", "--json"])
    assert args.command == "doctor"
    assert args.json is True


def test_manifest_command_parses() -> None:
    args = build_parser().parse_args(["validate-manifest", "dataset.yaml"])
    assert args.command == "validate-manifest"
    assert args.path == "dataset.yaml"


def test_capture_once_defaults_to_game_title() -> None:
    args = build_parser().parse_args(["capture-once"])
    assert args.title == "战舰世界"
    assert args.output is None
    assert args.backend == "printwindow"


def test_monitor_ui_is_read_only_by_default() -> None:
    args = build_parser().parse_args(["monitor-ui"])
    assert args.title == "战舰世界"
    assert args.backend == "printwindow"
    assert args.capture_fps == 2.0


def test_launcher_ui_uses_default_config() -> None:
    args = build_parser().parse_args(["launcher-ui"])
    assert args.command == "launcher-ui"
    assert args.config == "config/default.yaml"


def test_simulate_task_command_parses() -> None:
    args = build_parser().parse_args(["simulate-task", "scenario.yaml"])
    assert args.command == "simulate-task"
    assert args.path == "scenario.yaml"


def test_port_test_requires_explicit_live_confirmation() -> None:
    args = build_parser().parse_args(["port-test", "--ship", "那不勒斯"])
    assert args.ship == "那不勒斯"
    assert args.mode == "联合作战"
    assert args.confirm_live_input is False
    assert args.select_only is False
    assert args.continuous is False


def test_port_test_continuous_mode_parses() -> None:
    args = build_parser().parse_args(
        ["port-test", "--ship", "那不勒斯", "--continuous"]
    )
    assert args.continuous is True


def test_result_test_requires_explicit_live_confirmation() -> None:
    args = build_parser().parse_args(["result-test", "--action", "return_port"])
    assert args.action == "return_port"
    assert args.confirm_live_input is False


def test_validate_port_image_parses_expected_targets() -> None:
    args = build_parser().parse_args(
        ["validate-port-image", "port.png", "--ship", "那不勒斯"]
    )
    assert args.path == "port.png"
    assert args.ship == "那不勒斯"
    assert args.mode == "联合作战"
