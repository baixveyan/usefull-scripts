from wows_assistant.diagnostics.doctor import CheckResult, DoctorReport


def test_report_requires_all_required_checks() -> None:
    checks = (
        CheckResult("required", True, "ok"),
        CheckResult("optional", False, "missing", required=False),
    )
    report = DoctorReport(
        ok=all(check.ok for check in checks if check.required),
        checks=checks,
    )
    assert report.ok is True

