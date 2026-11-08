from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import cv2

from wows_assistant.capture.windows import WindowsCapture, find_windows, save_frame, select_window
from wows_assistant.dataset import DatasetManifest
from wows_assistant.diagnostics.doctor import print_report, run_doctor
from wows_assistant.perception.debug import annotate_scene
from wows_assistant.perception.ocr import OcrEngine
from wows_assistant.perception.scene import SceneClassifier
from wows_assistant.replay import summarize_replay
from wows_assistant.tasks.simulator import TaskScenario, simulate_task


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wows-assistant")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="检查 Python、视觉库和 GPU 环境")
    doctor.add_argument("--json", action="store_true", help="输出 JSON")

    manifest = subparsers.add_parser("validate-manifest", help="验证离线数据集清单")
    manifest.add_argument("path", help="YAML 清单路径")

    replay = subparsers.add_parser("replay-summary", help="汇总 JSONL 回放日志")
    replay.add_argument("path", help="JSONL 日志路径")

    windows = subparsers.add_parser("list-windows", help="只读列出匹配的可见窗口")
    windows.add_argument("--title", default="战舰世界", help="标题包含文本")

    capture = subparsers.add_parser("capture-once", help="只读截取一次窗口客户区")
    capture.add_argument("--title", default="战舰世界", help="标题包含文本")
    capture.add_argument("--output", help="PNG 输出路径")
    capture.add_argument(
        "--backend",
        choices=("printwindow", "screen"),
        default="printwindow",
        help="printwindow 可截被遮挡窗口；screen 只允许前台窗口",
    )

    analyze = subparsers.add_parser("analyze-image", help="OCR 并分析离线图片场景")
    analyze.add_argument("path", help="待分析图片")
    analyze.add_argument("--annotated", help="带识别框的调试图片输出路径")

    validate_port = subparsers.add_parser(
        "validate-port-image", help="离线验证港口截图中的舰船、模式和加入战斗按钮"
    )
    validate_port.add_argument("path", help="港口截图路径")
    validate_port.add_argument("--ship", required=True)
    validate_port.add_argument("--mode", default="联合作战")

    monitor = subparsers.add_parser("monitor-ui", help="启动严格只读的实时监控界面")
    monitor.add_argument("--title", default="战舰世界", help="标题包含文本")
    monitor.add_argument("--capture-fps", type=float, default=2.0)
    monitor.add_argument("--ocr-interval", type=float, default=5.0, help="两次 OCR 之间的等待秒数")
    monitor.add_argument("--backend", choices=("printwindow", "screen"), default="printwindow")

    launcher = subparsers.add_parser("launcher-ui", help="启动舰船与战斗模式控制面板")
    launcher.add_argument("--config", default="config/default.yaml")

    simulate = subparsers.add_parser("simulate-task", help="使用 YAML 场景执行纯 Dry Run 状态机")
    simulate.add_argument("path", help="场景 YAML 路径")

    port_test = subparsers.add_parser("port-test", help="按舰名准备并加入一局，仅测试到进入战斗")
    port_test.add_argument("--ship", required=True, help="可见舰船名称，例如那不勒斯")
    port_test.add_argument("--mode", default="联合作战")
    port_test.add_argument("--title", default="战舰世界")
    port_test.add_argument("--wait-timeout", type=float, default=300.0)
    port_test.add_argument("--config", default="config/default.yaml")
    port_test.add_argument("--select-only", action="store_true", help="确认选船和模式后停止，不加入战斗")
    port_test.add_argument(
        "--navigate-map-center",
        action="store_true",
        help="开局后识别战术地图己方白色三角，并点击纵向正对面区域",
    )
    port_test.add_argument(
        "--return-port-after-battle",
        action="store_true",
        help="战斗结算后点击回到港口并确认闭环",
    )
    port_test.add_argument("--battle-end-timeout", type=float, default=1800.0)
    port_test.add_argument(
        "--continuous",
        action="store_true",
        help="每局回港并确认后重复完整流程，直到停止或验证失败",
    )
    port_test.add_argument(
        "--confirm-live-input",
        action="store_true",
        help="显式允许聚焦游戏并执行受控点击；省略时只做定位预检",
    )

    result_test = subparsers.add_parser("result-test", help="测试结算页返回港口或继续战斗")
    result_test.add_argument("--action", choices=("return_port", "continue_battle"), required=True)
    result_test.add_argument("--title", default="战舰世界")
    result_test.add_argument("--wait-timeout", type=float, default=120.0)
    result_test.add_argument("--confirm-live-input", action="store_true")

    resume = subparsers.add_parser("battle-resume", help="加入战斗后续接等待与单次地图导航")
    resume.add_argument("--title", default="战舰世界")
    resume.add_argument("--wait-timeout", type=float, default=600.0)
    resume.add_argument("--battle-end-timeout", type=float, default=1800.0)
    resume.add_argument("--return-port-after-battle", action="store_true")
    resume.add_argument("--config", default="config/default.yaml")
    resume.add_argument("--confirm-live-input", action="store_true", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        report = run_doctor()
        print_report(report, as_json=args.json)
        return 0 if report.ok else 1
    if args.command == "validate-manifest":
        manifest = DatasetManifest.load(args.path)
        missing = manifest.validate_files(args.path)
        print(json.dumps({"name": manifest.name, "samples": len(manifest.samples), "missing": [str(path) for path in missing]}, ensure_ascii=False, indent=2))
        return 1 if missing else 0
    if args.command == "replay-summary":
        print(json.dumps(summarize_replay(args.path), ensure_ascii=False, indent=2))
        return 0
    if args.command == "list-windows":
        windows = find_windows(args.title)
        payload = [
            {
                "hwnd": window.hwnd,
                "title": window.title,
                "process_id": window.process_id,
                "minimized": window.minimized,
                "client": {
                    "left": window.client.left,
                    "top": window.client.top,
                    "width": window.client.width,
                    "height": window.client.height,
                },
            }
            for window in windows
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if windows else 1
    if args.command == "capture-once":
        window = select_window(args.title)
        frame = WindowsCapture().capture(window, backend=args.backend)
        output = Path(args.output) if args.output else Path("outputs") / "captures" / (
            datetime.now(UTC).strftime("capture-%Y%m%d-%H%M%S.png")
        )
        saved = save_frame(frame, output)
        print(
            json.dumps(
                {
                    "path": str(saved.resolve()),
                    "window": window.title,
                    "hwnd": window.hwnd,
                    "width": frame.ref.width,
                    "height": frame.ref.height,
                    "backend": args.backend,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "analyze-image":
        image = cv2.imread(str(Path(args.path)))
        if image is None:
            raise FileNotFoundError(args.path)
        ocr_run = OcrEngine().recognize(image)
        classification = SceneClassifier().classify(ocr_run.results)
        if args.annotated:
            annotated = annotate_scene(image, classification, ocr=ocr_run.results)
            output = Path(args.annotated)
            output.parent.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(output), annotated):
                raise OSError(f"无法写入调试图片: {output}")
        print(
            json.dumps(
                {
                    "scene": classification.scene.value,
                    "confidence": round(classification.confidence, 4),
                    "evidence": classification.evidence,
                    "scores": {
                        scene.value: round(score, 4)
                        for scene, score in classification.scores.items()
                    },
                    "ocr_count": len(ocr_run.results),
                    "ocr_elapsed_ms": round(ocr_run.elapsed_ms, 2),
                    "annotated": str(Path(args.annotated).resolve()) if args.annotated else None,
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0
    if args.command == "validate-port-image":
        from wows_assistant.models import BoundingBox, Scene
        from wows_assistant.tasks.port_flow import find_text_target

        image = cv2.imread(str(Path(args.path)))
        if image is None:
            raise FileNotFoundError(args.path)
        ocr_run = OcrEngine().recognize(image)
        classification = SceneClassifier().classify(ocr_run.results)
        checks: dict[str, bool] = {"scene_port": classification.scene is Scene.PORT}
        targets = {
            "ship": (args.ship, BoundingBox(x1=0.0, y1=0.55, x2=1.0, y2=1.0)),
            "mode": (args.mode, BoundingBox(x1=0.45, y1=0.0, x2=0.75, y2=0.12)),
            "join_battle": (
                "加入战斗",
                BoundingBox(x1=0.25, y1=0.0, x2=0.75, y2=0.12),
            ),
        }
        locations: dict[str, tuple[int, int] | None] = {}
        height, width = image.shape[:2]
        for name, (query, region) in targets.items():
            try:
                target = find_text_target(query, ocr_run.results, region=region)
                locations[name] = target.center_pixels(width, height)
                checks[name] = True
            except LookupError:
                locations[name] = None
                checks[name] = False
        passed = all(checks.values())
        print(json.dumps({
            "passed": passed,
            "checks": checks,
            "locations": locations,
            "scene": classification.scene.value,
            "scene_confidence": round(classification.confidence, 4),
            "ocr_count": len(ocr_run.results),
            "ocr_elapsed_ms": round(ocr_run.elapsed_ms, 2),
        }, ensure_ascii=True, indent=2))
        return 0 if passed else 1
    if args.command == "monitor-ui":
        from PyQt5 import QtCore, QtWidgets

        from wows_assistant.monitor import ReadOnlyMonitorController
        from wows_assistant.ui.monitor import MonitorWindow

        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        app = QtWidgets.QApplication([])
        window_info = select_window(args.title)
        controller = ReadOnlyMonitorController(
            window_info,
            capture_fps=args.capture_fps,
            ocr_interval_seconds=args.ocr_interval,
            backend=args.backend,
        )
        window = MonitorWindow(controller, Path("outputs") / "debug")
        window.show()
        return int(app.exec_())
    if args.command == "launcher-ui":
        from PyQt5 import QtCore, QtWidgets

        from wows_assistant.ui.launcher import LauncherWindow

        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        app = QtWidgets.QApplication([])
        window = LauncherWindow(config_path=args.config)
        window.show()
        return int(app.exec_())
    if args.command == "simulate-task":
        result = simulate_task(TaskScenario.load(args.path))
        transitions = [
            {
                "from": decision.transition.previous.value,
                "to": decision.transition.current.value,
                "reason": decision.transition.reason,
            }
            for decision in result.decisions
            if decision.transition is not None
        ]
        print(
            json.dumps(
                {
                    "scenario": result.scenario,
                    "final_state": result.final.state.value,
                    "battles_completed": result.final.battles_completed,
                    "transitions": transitions,
                    "dry_run_actions": [
                        {
                            "kind": record.intent.kind.value,
                            "reason": record.intent.reason,
                            "parameters": record.intent.parameters,
                            "executed": record.executed,
                            "status": record.status,
                        }
                        for record in result.executions
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0
    if args.command == "port-test":
        from wows_assistant.config import NavigationConfig
        from wows_assistant.tasks.port_flow import PortBattleFlow

        run_name = datetime.now(UTC).strftime("port-test-%Y%m%d-%H%M%S")
        output_dir = Path("outputs") / "port-tests" / run_name
        flow = PortBattleFlow(
            select_window(args.title),
            output_dir=output_dir,
            live_input=args.confirm_live_input,
            navigation=NavigationConfig.load(args.config),
        )
        cycle = 0
        resume_next_battle = False
        while True:
            if resume_next_battle:
                result = flow.resume_wait_and_navigate(
                    timeout_seconds=args.wait_timeout,
                    navigate_map_center=args.navigate_map_center,
                    return_port_after_battle=False,
                    battle_end_timeout_seconds=args.battle_end_timeout,
                    continue_battle_after_result=True,
                )
            else:
                result = flow.run(
                    ship_name=args.ship,
                    mode_name=args.mode,
                    wait_timeout_seconds=args.wait_timeout,
                    select_only=args.select_only,
                    navigate_map_center=args.navigate_map_center,
                    continue_battle_after_result=args.continuous,
                    return_port_after_battle=(
                        args.return_port_after_battle and not args.continuous
                    ),
                    battle_end_timeout_seconds=args.battle_end_timeout,
                )
            cycle += 1
            if args.continuous:
                print(
                    json.dumps(
                        {
                            "event": "cycle_finished",
                            "cycle": cycle,
                            "status": result.status,
                            "scene": result.scene.value,
                            "message": result.message,
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
            if args.continuous and result.status == "continue_battle_clicked":
                resume_next_battle = True
                continue
            if not args.continuous or result.status != "cycle_completed":
                break
        print(
            json.dumps(
                {
                    "status": result.status,
                    "scene": result.scene.value,
                    "message": result.message,
                    "live_input": args.confirm_live_input,
                    "clicks": result.clicks,
                    "screenshots": result.screenshots,
                    "output_dir": str(output_dir.resolve()),
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0 if result.status in {
            "dry_run_ready",
            "ship_selected",
            "battle_entered",
            "navigation_started",
            "cycle_completed",
            "continue_battle_clicked",
        } else 1
    if args.command == "result-test":
        from wows_assistant.tasks.result_flow import BattleResultFlow

        run_name = datetime.now(UTC).strftime("result-test-%Y%m%d-%H%M%S")
        output_dir = Path("outputs") / "result-tests" / run_name
        result = BattleResultFlow(
            select_window(args.title), output_dir=output_dir, live_input=args.confirm_live_input
        ).run(args.action, timeout_seconds=args.wait_timeout)
        print(json.dumps({
            "status": result.status,
            "scene": result.scene.value,
            "action": result.action,
            "executed": result.executed,
            "screenshots": result.screenshots,
            "output_dir": str(output_dir.resolve()),
        }, ensure_ascii=True, indent=2))
        return 0 if result.status in {"dry_run_ready", "verified"} else 1
    if args.command == "battle-resume":
        from wows_assistant.config import NavigationConfig
        from wows_assistant.tasks.port_flow import PortBattleFlow

        run_name = datetime.now(UTC).strftime("battle-resume-%Y%m%d-%H%M%S")
        output_dir = Path("outputs") / "battle-resumes" / run_name
        result = PortBattleFlow(
            select_window(args.title),
            output_dir=output_dir,
            live_input=True,
            navigation=NavigationConfig.load(args.config),
        ).resume_wait_and_navigate(
            timeout_seconds=args.wait_timeout,
            return_port_after_battle=args.return_port_after_battle,
            battle_end_timeout_seconds=args.battle_end_timeout,
        )
        print(json.dumps({
            "status": result.status,
            "scene": result.scene.value,
            "message": result.message,
            "clicks": result.clicks,
            "screenshots": result.screenshots,
            "output_dir": str(output_dir.resolve()),
        }, ensure_ascii=True, indent=2))
        return 0 if result.status in {"navigation_started", "cycle_completed"} else 1
    return 2
