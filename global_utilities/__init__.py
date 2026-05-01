from __future__ import annotations

from .logger import error, info, success, warn

__all__ = [
    "SimulationJsonMetadata",
    "SimulationJsonObjects",
    "PIPE_DIR_NAME",
    "error",
    "info",
    "read_simulation_ready_json",
    "resolve_pipe_path",
    "success",
    "warn",
    "write_simulation_ready_json",
]


def __getattr__(name: str):
    if name in {
        "SimulationJsonMetadata",
        "SimulationJsonObjects",
        "PIPE_DIR_NAME",
        "read_simulation_ready_json",
        "resolve_pipe_path",
        "write_simulation_ready_json",
    }:
        from . import json_io

        return getattr(json_io, name)
    raise AttributeError(f"module 'global_utilities' has no attribute '{name}'")
