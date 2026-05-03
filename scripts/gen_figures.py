#!/usr/bin/env python3
"""
Generate SVG + PNG figures referenced from README.md.

Run from repo root:
  python scripts/gen_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt

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
    labels = ["BiCS 8\n(~218 layers)", "BiCS 10\n(332 layers)"]
    values = [218, 332]
    colors = [COLORS["bics_8"], COLORS["bics_10"]]

    fig, ax = plt.subplots(figsize=(11.0, 4.6), dpi=150)
    y = range(len(labels))
    bars = ax.barh(y, values, height=0.55, color=colors, edgecolor="white", linewidth=1.2)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Vertical layer count (public roadmap figures)")
    ax.set_title("BiCS FLASH: published vertical layer counts (8th and 10th generations)")
    ax.set_xlim(0, max(values) * 1.12)
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
    ax.axvline(218, color=COLORS["muted"], linestyle="--", linewidth=0.8, alpha=0.5, zorder=0)
    ax.text(
        0.02,
        -0.32,
        "BiCS 9 is in development; public layer count is not in the roadmap table above, so it is omitted here.",
        transform=ax.transAxes,
        fontsize=8,
        color=COLORS["muted"],
        va="top",
    )
    fig.tight_layout()
    _save_both(fig, out_dir / "bics-layers")
    plt.close(fig)


def figure_model_footprint(out_dir: Path) -> None:
    """Compressed weight footprint (MB) vs typical controller DRAM pool (1 to 4 GB band)."""
    models = [
        "TinyML / MobileNet\n(<100M params, 8/4-bit)",
        "Llama-3.2-1B\n(2-bit / ternary, ~200 to 300 MB)",
        "Phi-3.5-mini\n(1.58-bit BitNet, ~600 MB)",
    ]
    # Midpoint for Llama range; cap for TinyML; cited ~600 for Phi
    sizes_mb = [50, 250, 600]
    colors = [COLORS["tiny"], COLORS["llama"], COLORS["phi"]]
    dram_min_mb = 1024  # 1 GB
    dram_max_mb = 4096  # 4 GB

    fig, ax = plt.subplots(figsize=(14.0, 7.5), dpi=150)
    x = list(range(len(models)))
    # Log scale so bars and multi-GB DRAM envelope share one readable chart
    ax.set_yscale("log")
    ax.set_ylim(40, 6000)
    ax.axhspan(
        dram_min_mb,
        dram_max_mb,
        color="#bbf7d0",
        alpha=0.35,
        zorder=0,
        label="Typical DRAM pool (1 to 4 GB, see README table)",
    )
    ax.axhline(
        100,
        color=COLORS["muted"],
        linestyle="--",
        linewidth=0.9,
        alpha=0.7,
        label="~100 MB buffer reference (TinyLM subsection)",
    )
    bars = ax.bar(x, sizes_mb, color=colors, edgecolor="white", linewidth=1.2, width=0.62, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=11)
    ax.set_ylabel("Size (MB), log scale")
    ax.set_title("Quantized weight footprint (MB) vs controller DRAM envelope")
    for bar, val in zip(bars, sizes_mb):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val * 1.12,
            f"{val}",
            ha="center",
            va="bottom",
            fontsize=11,
            color=COLORS["text"],
            zorder=3,
        )
    ax.legend(loc="upper left", fontsize=10, framealpha=0.92, borderaxespad=0.5)
    ax.text(
        0.02,
        -0.38,
        "Each bar is one model's compressed weights. The green band is the typical total controller "
        "DRAM range (1 to 4 GB) from the README table: compare bar height to that pool (firmware and "
        "I/O also use DRAM). Log scale fits MB-scale weights and GB-scale DRAM on one axis. No single "
        "best footprint, see latency and reasoning tradeoffs in the README table. Llama uses the "
        "~200 to 300 MB midpoint.",
        transform=ax.transAxes,
        fontsize=9,
        color=COLORS["muted"],
        va="top",
    )
    fig.subplots_adjust(bottom=0.32)
    _save_both(fig, out_dir / "model-footprint-mb")
    plt.close(fig)


def figure_memory_ladder(out_dir: Path) -> None:
    """Log-scale comparison: on-chip SRAM vs controller DRAM envelope (orders of magnitude)."""
    labels = ["On-chip SRAM\n(per core, TCM)", "System DRAM\n(controller envelope)"]
    # Representative points: <1 MB vs 1–4 GB → use 0.5 MB and 2 GB midpoint for visualization
    bytes_vals = [0.5 * 1024**2, 2 * 1024**3]
    colors = ["#fde68a", "#a5b4fc"]

    fig, ax = plt.subplots(figsize=(11.0, 5.0), dpi=150)
    x = range(len(labels))
    ax.bar(x, bytes_vals, color=colors, edgecolor="white", linewidth=1.2, width=0.55)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Bytes (log scale)")
    ax.set_yscale("log")
    ax.set_title("Memory hierarchy gap on SSD controllers (illustrative)")
    ymin = 10**5
    ymax = 5 * 10**10
    ax.set_ylim(ymin, ymax)
    fmt_labels = ["< 1 MB class", "~2 GB (mid of 1 to 4 GB range)"]
    for i, (v, fl) in enumerate(zip(bytes_vals, fmt_labels)):
        ax.text(i, v * 1.35, fl, ha="center", va="bottom", fontsize=10, color=COLORS["text"])
    ax.text(
        0.02,
        -0.24,
        "Illustrative only: weight tiles exceed SRAM and stress DRAM headroom, which motivates quantization.",
        transform=ax.transAxes,
        fontsize=8,
        color=COLORS["muted"],
        va="top",
    )
    fig.tight_layout()
    _save_both(fig, out_dir / "memory-hierarchy-log")
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
    figure_memory_ladder(out_dir)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
