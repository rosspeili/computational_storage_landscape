#!/usr/bin/env python3
"""
Generate SVG + PNG figures referenced from README.md.

Run from repo root:
  python scripts/gen_figures.py

Policy:
  - Explanatory prose belongs in README.md as italic lines *under* each figure — not inside PNG/SVG.
  - Never draw footer notes or narrative under the plot area (no ax.text/fig.text in negative y /
    transAxes bottom band, no “story” captions inside the file).
  - In-chart text is only: short title, axis labels, tick labels, data labels on bars (numbers),
    and plot geometry (bars, lines, bands).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

# Pastel palette aligned with README badges / skillware-style tones
COLORS = {
    "bics_8": "#bae6fd",
    "bics_10": "#bbf7d0",
    "tiny": "#fdf2f8",
    "llama": "#ddd6fe",
    "phi": "#fecaca",
    "text": "#1e293b",
    "muted": "#64748b",
    "grid": "#e2e8f0",
}


def _mb_tick_linear(val: float, _pos: int | None = None) -> str:
    """Axis ticks for linear MB scales (single unit, no GB switching)."""
    if abs(val - round(val)) < 1e-6:
        return f"{int(round(val))} MB"
    return f"{val:g} MB"


def _setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": COLORS["grid"],
            "axes.labelcolor": COLORS["text"],
            "text.color": COLORS["text"],
            "xtick.color": COLORS["text"],
            "ytick.color": COLORS["text"],
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "axes.titleweight": "600",
            "legend.fontsize": 10,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )


def figure_bics_layers(out_dir: Path) -> None:
    """BiCS 8 and BiCS 10 public layer counts (BiCS 9 developing, not plotted numerically)."""
    labels = ["BiCS 8", "BiCS 10"]
    values = [218, 332]
    colors = [COLORS["bics_8"], COLORS["bics_10"]]

    fig, ax = plt.subplots(figsize=(10.0, 3.8), dpi=150)
    ax.set_axisbelow(True)
    y = range(len(labels))
    bars = ax.barh(y, values, height=0.55, color=colors, edgecolor="white", linewidth=1.2)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Layers")
    ax.set_title("BiCS FLASH: public vertical layer counts (8th and 10th gen)", fontsize=12, pad=10)
    ax.set_xlim(0, max(values) * 1.12)
    ax.xaxis.set_major_locator(MultipleLocator(50))
    ax.grid(axis="x", alpha=0.28, linestyle="-", linewidth=0.6, color=COLORS["grid"], zorder=0)
    for bar, val in zip(bars, values):
        ax.text(
            val + 8,
            bar.get_y() + bar.get_height() / 2,
            f"{val}",
            va="center",
            ha="left",
            fontsize=11,
            color=COLORS["text"],
        )
    ax.axvline(218, color=COLORS["muted"], linestyle="--", linewidth=0.9, alpha=0.65, zorder=0)
    fig.tight_layout()
    _save_both(fig, out_dir / "bics-layers")
    plt.close(fig)


def figure_model_footprint(out_dir: Path) -> None:
    """Compressed weight footprint (MB, linear) vs typical controller DRAM pool (1 to 4 GB band)."""
    models = ["TinyML / MobileNet", "Llama-3.2-1B", "Phi-3.5-mini"]
    sizes_mb = [50, 250, 600]
    colors = [COLORS["tiny"], COLORS["llama"], COLORS["phi"]]
    dram_min_mb = 1024
    dram_max_mb = 4096
    y_max = 4400

    fig, ax = plt.subplots(figsize=(9.0, 5.4), dpi=150)
    x = list(range(len(models)))
    ax.set_axisbelow(True)
    ax.axhspan(dram_min_mb, dram_max_mb, color="#bbf7d0", alpha=0.38, zorder=0)
    bars = ax.bar(x, sizes_mb, color=colors, edgecolor="white", linewidth=1.2, width=0.62, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=11)
    ax.set_ylim(0, y_max)
    ax.set_ylabel("Compressed weight size (MB)")
    ax.set_title("Compressed weights vs controller DRAM range", fontsize=12, pad=10)
    ax.yaxis.set_major_formatter(FuncFormatter(_mb_tick_linear))
    ax.set_yticks([0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000])
    ax.grid(True, axis="y", which="major", alpha=0.28, linestyle="-", linewidth=0.6, zorder=1)
    for bar, val in zip(bars, sizes_mb):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 120,
            f"{val}",
            ha="center",
            va="bottom",
            fontsize=11,
            color=COLORS["text"],
            zorder=3,
        )
    ax.tick_params(axis="both", labelsize=10)
    fig.tight_layout()
    _save_both(fig, out_dir / "model-footprint-mb")
    plt.close(fig)


def figure_memory_hierarchy(out_dir: Path) -> None:
    """SRAM vs DRAM on linear MB axes (zoomed SRAM + full DRAM pool from README hardware table)."""
    sram_mb = 0.5
    dram_mid_mb = 2048.0
    dram_min_mb = 1024
    dram_max_mb = 4096
    sram_ymax = 1.15
    dram_ymax = 4600

    fig, (ax_s, ax_d) = plt.subplots(
        1,
        2,
        figsize=(10.0, 5.0),
        dpi=150,
        layout="constrained",
        gridspec_kw={"width_ratios": [1.05, 1.2]},
    )
    fig.suptitle("On-controller memory: SRAM vs DRAM (linear MB)", fontsize=13, fontweight="600")

    ax_s.set_axisbelow(True)
    bars_s = ax_s.bar([0], [sram_mb], width=0.55, color="#fde68a", edgecolor="white", linewidth=1.2)
    ax_s.set_xticks([0])
    ax_s.set_xticklabels(["SRAM"], fontsize=10)
    ax_s.set_ylim(0, sram_ymax)
    ax_s.set_ylabel("Capacity (MB)")
    ax_s.set_title("On-chip SRAM (illustrative)", fontsize=11, pad=8)
    ax_s.yaxis.set_major_formatter(FuncFormatter(_mb_tick_linear))
    ax_s.grid(True, axis="y", alpha=0.28, linestyle="-", linewidth=0.6)
    ax_s.text(
        0,
        sram_mb + 0.06,
        "0.5",
        ha="center",
        va="bottom",
        fontsize=11,
        color=COLORS["text"],
    )

    ax_d.set_axisbelow(True)
    ax_d.axhspan(dram_min_mb, dram_max_mb, color="#bbf7d0", alpha=0.35, zorder=0)
    ax_d.bar([0], [dram_mid_mb], width=0.55, color="#a5b4fc", edgecolor="white", linewidth=1.2, zorder=2)
    ax_d.set_xticks([0])
    ax_d.set_xticklabels(["DRAM"], fontsize=10)
    ax_d.set_ylim(0, dram_ymax)
    ax_d.set_ylabel("Capacity (MB)")
    ax_d.set_title("System DRAM (controller pool)", fontsize=11, pad=8)
    ax_d.yaxis.set_major_formatter(FuncFormatter(_mb_tick_linear))
    ax_d.set_yticks([0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000])
    ax_d.grid(True, axis="y", which="major", alpha=0.28, linestyle="-", linewidth=0.6, zorder=1)
    ax_d.text(
        0,
        dram_mid_mb + 150,
        "2048",
        ha="center",
        va="bottom",
        fontsize=11,
        color=COLORS["text"],
        zorder=3,
    )

    fig.set_constrained_layout_pads(w_pad=0.05, h_pad=0.02, hspace=0, wspace=0.05)
    _save_both(fig, out_dir / "memory-hierarchy-mb")
    plt.close(fig)


def _save_both(fig: plt.Figure, base_path: Path) -> None:
    base_path.parent.mkdir(parents=True, exist_ok=True)
    png = base_path.with_suffix(".png")
    svg = base_path.with_suffix(".svg")
    fig.savefig(png, dpi=240, bbox_inches="tight", facecolor="white")
    fig.savefig(svg, bbox_inches="tight", facecolor="white")
    print(f"Wrote {png}")
    print(f"Wrote {svg}")


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    out_dir = root / "figures"
    _setup_style()
    figure_bics_layers(out_dir)
    figure_model_footprint(out_dir)
    figure_memory_hierarchy(out_dir)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())