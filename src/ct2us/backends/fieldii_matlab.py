"""Genuine Field II 3.x backend driven through the MATLAB Engine for Python."""
from __future__ import annotations

from pathlib import Path
import os

import numpy as np


class FieldIIMatlabBackend:
    """Generate pulse-echo RF lines with Field II's official MATLAB MEX API.

    Field II is MATLAB MEX software. This backend intentionally has no Python
    approximation: it starts MATLAB, calls ``field_init`` and ``calc_scat`` for
    every focused line, and returns the resulting Field II RF data.
    """

    name = "fieldii_matlab"

    def __init__(self, fieldii_root: str | Path | None = None):
        project_root = Path(__file__).resolve().parents[3]
        default_root = project_root / "third_party" / "Field_II-3.30"
        self.fieldii_root = Path(
            fieldii_root or os.environ.get("FIELD_II_ROOT", default_root)
        ).expanduser().resolve()

    @staticmethod
    def _matlab():
        try:
            import matlab  # type: ignore[import-not-found]
            import matlab.engine  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "The genuine Field II backend needs MATLAB and the MATLAB Engine "
                "API for Python in this environment. Install the engine using the "
                "instructions in README.md, then rerun with backend.name: "
                "fieldii_matlab."
            ) from exc
        return matlab, matlab.engine

    @staticmethod
    def _vector(matlab, values: np.ndarray):
        return matlab.double(np.asarray(values, dtype=float).reshape(1, -1).tolist())

    @staticmethod
    def _copy_line(target: np.ndarray, line: np.ndarray, start: int) -> None:
        source_start = max(0, -start)
        target_start = max(0, start)
        count = min(len(line) - source_start, len(target) - target_start)
        if count > 0:
            target[target_start:target_start + count] = line[source_start:source_start + count]

    def simulate(self, positions_m, amplitudes, acquisition, mean_speed_m_s):
        matlab, matlab_engine = self._matlab()
        if not self.fieldii_root.is_dir() or not (self.fieldii_root / "Mat_field.mexa64").is_file():
            raise RuntimeError(
                f"Official Field II Linux files were not found at {self.fieldii_root}. "
                "Set FIELD_II_ROOT to the extracted Field II distribution."
            )

        fs = float(acquisition["sampling_frequency_hz"])
        fc = float(acquisition["center_frequency_hz"])
        speed = float(mean_speed_m_s)
        elements = int(acquisition["element_count"])
        width = float(acquisition["element_width_mm"]) / 1000.0
        height = float(acquisition["element_height_mm"]) / 1000.0
        kerf = float(acquisition["element_kerf_mm"]) / 1000.0
        tx_focus = float(acquisition["transmit_focus_mm"]) / 1000.0
        rx_focus = float(acquisition["receive_focus_mm"]) / 1000.0
        depth = float(acquisition["depth_mm"]) / 1000.0
        lines = int(acquisition["scan_lines"])
        samples = int(np.ceil(2 * depth / speed * fs))

        scatterers = np.column_stack([
            np.asarray(positions_m, dtype=float)[:, 0],
            np.zeros(len(positions_m), dtype=float),
            np.asarray(positions_m, dtype=float)[:, 1],
        ])
        scatterers_m = matlab.double(scatterers.tolist())
        amplitudes_m = matlab.double(np.asarray(amplitudes, dtype=float).reshape(-1, 1).tolist())
        waveform_t = np.arange(0.0, 2.0 / fc + 0.5 / fs, 1.0 / fs)
        waveform = np.sin(2 * np.pi * fc * waveform_t)
        impulse = waveform * np.hanning(len(waveform))
        focus = matlab.double([[0.0, 0.0, tx_focus]])
        line_x = np.linspace(
            -float(acquisition["lateral_extent_mm"]) / 2000.0,
            float(acquisition["lateral_extent_mm"]) / 2000.0,
            lines,
        )
        rf = np.zeros((lines, samples), dtype=np.float32)

        engine = matlab_engine.start_matlab()
        tx = rx = None
        try:
            engine.addpath(str(self.fieldii_root), nargout=0)
            engine.field_init(0.0, nargout=0)
            engine.set_field("c", speed, nargout=0)
            engine.set_sampling(fs, nargout=0)
            tx = engine.xdc_linear_array(elements, width, height, kerf, 1.0, 1.0, focus, nargout=1)
            rx = engine.xdc_linear_array(elements, width, height, kerf, 1.0, 1.0, focus, nargout=1)
            engine.xdc_impulse(tx, self._vector(matlab, impulse), nargout=0)
            engine.xdc_impulse(rx, self._vector(matlab, impulse), nargout=0)
            engine.xdc_excitation(tx, self._vector(matlab, waveform), nargout=0)
            for line_index, x in enumerate(line_x):
                center = matlab.double([[float(x), 0.0, 0.0]])
                tx_target = matlab.double([[float(x), 0.0, tx_focus]])
                rx_target = matlab.double([[float(x), 0.0, rx_focus]])
                # xdc_center_focus takes only the aperture and reference point;
                # the time argument belongs to xdc_focus.
                engine.xdc_center_focus(tx, center, nargout=0)
                engine.xdc_center_focus(rx, center, nargout=0)
                engine.xdc_focus(tx, 0.0, tx_target, nargout=0)
                engine.xdc_focus(rx, 0.0, rx_target, nargout=0)
                response, start_time = engine.calc_scat(tx, rx, scatterers_m, amplitudes_m, nargout=2)
                line = np.asarray(response, dtype=np.float32).reshape(-1)
                self._copy_line(rf[line_index], line, int(round(float(start_time) * fs)))
        finally:
            if tx is not None:
                engine.xdc_free(tx, nargout=0)
            if rx is not None:
                engine.xdc_free(rx, nargout=0)
            engine.field_end(nargout=0)
            engine.quit()
        return rf
