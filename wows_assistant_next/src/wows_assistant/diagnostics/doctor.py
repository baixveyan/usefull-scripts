from __future__ import annotations

import importlib
import json
import os
import platform
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str
    required: bool = True


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    checks: tuple[CheckResult, ...]


def _check_import(name: str, module_name: str | None = None) -> CheckResult:
    module_name = module_name or name
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", "已导入")
        return CheckResult(name, True, str(version))
    except Exception as exc:  # diagnostics must report all failures
        return CheckResult(name, False, f"{type(exc).__name__}: {exc}")


def _check_python() -> CheckResult:
    version = sys.version_info
    ok = version.major == 3 and version.minor == 11
    return CheckResult("Python", ok, f"{platform.python_version()} @ {sys.executable}")


def _check_conda() -> CheckResult:
    env = os.environ.get("CONDA_DEFAULT_ENV", "未通过 conda activate 设置")
    prefix = os.environ.get("CONDA_PREFIX", sys.prefix)
    ok = env == "scripts" or os.path.basename(prefix).lower() == "scripts"
    return CheckResult("Conda 环境", ok, f"name={env}, prefix={prefix}")


def _check_torch_cuda() -> CheckResult:
    try:
        import torch

        if not torch.cuda.is_available():
            return CheckResult("PyTorch CUDA", False, f"torch={torch.__version__}, CUDA 不可用")
        device = torch.cuda.get_device_name(0)
        capability = torch.cuda.get_device_capability(0)
        x = torch.tensor([1.0, 2.0, 3.0], device="cuda")
        value = float((x * x).sum().item())
        ok = value == 14.0
        detail = (
            f"torch={torch.__version__}, runtime={torch.version.cuda}, "
            f"device={device}, capability={capability}, smoke={value}"
        )
        return CheckResult("PyTorch CUDA", ok, detail)
    except Exception as exc:
        return CheckResult("PyTorch CUDA", False, f"{type(exc).__name__}: {exc}")


def _check_onnx() -> CheckResult:
    try:
        import onnxruntime as ort

        providers = ort.get_available_providers()
        ok = "CPUExecutionProvider" in providers
        return CheckResult("ONNX Runtime", ok, f"{ort.__version__}; providers={providers}")
    except Exception as exc:
        return CheckResult("ONNX Runtime", False, f"{type(exc).__name__}: {exc}")


def _check_mss() -> CheckResult:
    try:
        import mss

        # Construction checks the Windows capture backend without taking a screenshot.
        with mss.mss() as capture:
            monitor_count = max(0, len(capture.monitors) - 1)
        return CheckResult("Windows 截图后端", monitor_count > 0, f"显示器数量={monitor_count}")
    except Exception as exc:
        return CheckResult("Windows 截图后端", False, f"{type(exc).__name__}: {exc}")


def run_doctor() -> DoctorReport:
    checks: list[CheckResult] = [
        _check_python(),
        _check_conda(),
        _check_import("NumPy", "numpy"),
        _check_import("OpenCV", "cv2"),
        _check_import("Pillow", "PIL"),
        _check_import("PyQt5", "PyQt5.QtCore"),
        _check_import("RapidOCR", "rapidocr_onnxruntime"),
        _check_import("pywin32", "win32api"),
        _check_onnx(),
        _check_mss(),
        _check_torch_cuda(),
    ]
    return DoctorReport(ok=all(check.ok for check in checks if check.required), checks=tuple(checks))


def print_report(report: DoctorReport, *, as_json: bool = False) -> None:
    if as_json:
        payload: dict[str, Any] = {
            "ok": report.ok,
            "checks": [asdict(check) for check in report.checks],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print("WoWS Assistant Next - 环境自检")
    print("=" * 50)
    for check in report.checks:
        marker = "OK" if check.ok else "FAIL"
        print(f"[{marker:4}] {check.name}: {check.detail}")
    print("=" * 50)
    print("结果：" + ("通过" if report.ok else "未通过"))
