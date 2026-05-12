"""High-level figure builders mapped to the 8 main figures of the paper.

Plan reference: Section H of /root/.claude/plans/token-token-quiet-bachman.md
"""

from __future__ import annotations

from pathlib import Path


def fig1_study_area(aoi_path: Path, dem_path: Path, jma_xy: tuple[float, float],
                    out: Path) -> None: raise NotImplementedError


def fig2_framework_flowchart(out: Path) -> None: raise NotImplementedError


def fig3_lulc_and_sankey(lulc_start: Path, lulc_end: Path,
                         transitions_csv: Path, out: Path) -> None: raise NotImplementedError


def fig4_wnsc_change(wnsc_start: Path, wnsc_end: Path,
                     out: Path) -> None: raise NotImplementedError


def fig5_luthi_bars(luthi_csv: Path, out: Path) -> None: raise NotImplementedError


def fig6_multiscale(luthi_csv: Path, out: Path) -> None: raise NotImplementedError


def fig7_shap(shap_long: Path, out: Path) -> None: raise NotImplementedError


def fig8_hipi(hipi_tif: Path, walk_lines: Path, out: Path) -> None: raise NotImplementedError
