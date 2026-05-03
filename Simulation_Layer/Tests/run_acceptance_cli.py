from __future__ import annotations

import builtins
from contextlib import redirect_stdout
from io import StringIO

from acceptance_helpers import (
    PROJECT_ROOT,
    acceptance_case_json_files,
    expected_winners_from_json,
    parse_cli_output,
    strip_ansi,
)
from Global_Utilities import success, warn
from Simulation_Layer.Runner.main import run_cli


def input_for(cli_path: str) -> str:
    print(cli_path)
    return cli_path


def run_cli_with_input(cli_path: str) -> tuple[int, dict]:
    original_input = builtins.input
    stdout_buffer = StringIO()
    exit_code = 0

    builtins.input = lambda: input_for(cli_path)
    try:
        with redirect_stdout(stdout_buffer):
            run_cli()
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    finally:
        builtins.input = original_input

    stdout = stdout_buffer.getvalue()
    print(stdout, end="")
    return exit_code, parse_cli_output(strip_ansi(stdout))


def main() -> int:
    failures: list[str] = []

    for json_path in acceptance_case_json_files():
        cli_path = json_path.relative_to(PROJECT_ROOT / "Pipe").as_posix()
        expected_winners = expected_winners_from_json(json_path)
        exit_code, result = run_cli_with_input(cli_path)
        actual_winners = result["winners"]

        if exit_code != 0:
            failure = f"{cli_path}: CLI exited with code {exit_code}"
            failures.append(failure)
            warn(failure)
            continue

        if actual_winners == expected_winners:
            success(f"{cli_path} winners match expected output: {actual_winners}")
            continue

        failure = (
            f"{cli_path}: expected winners {expected_winners}; "
            f"actual winners {actual_winners}"
        )
        failures.append(failure)
        warn(failure)

    if failures:
        warn(f"{len(failures)} CLI run(s) failed winner validation.")
        return 1

    success(
        f"CLI run completed for {len(acceptance_case_json_files())} "
        "acceptance cases."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
