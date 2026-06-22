"""
Generates a branded PNG news card for @Rokhaan.
Runs in the cloud (GitHub Actions) — no image software needed on your PC.
Clean, modern, data/text graphic (never a fake photo).
"""
import textwrap
import matplotlib
matplotlib.use("Agg")  # headless mode
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# Per-pillar accent colour + label
PILLAR_THEME = {
    "global":            {"accent": "#4da6ff", "label": "GLOBAL"},
    "us_foreign_policy": {"accent": "#ff5d73", "label": "US FOREIGN POLICY"},
    "afghanistan":       {"accent": "#2ecc71", "label": "AFGHANISTAN"},
    "worldcup":          {"accent": "#ffb627", "label": "WORLD CUP 2026"},
    "afghan_cricket":    {"accent": "#19d3a2", "label": "AFGHAN CRICKET"},
}
BG = "#0d1117"      # deep slate
PANEL = "#161b22"   # slightly lighter panel
MUTED = "#8b98a5"   # muted grey for secondary text


def make_card(pillar, headline, source, out_path="card.png"):
    """Create a 1200x675 (16:9) branded news card and save it to out_path."""
    theme = PILLAR_THEME.get(pillar, PILLAR_THEME["global"])
    accent = theme["accent"]

    fig = plt.figure(figsize=(12, 6.75), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(BG)

    # Rounded inner panel
    ax.add_patch(FancyBboxPatch(
        (0.04, 0.06), 0.92, 0.88,
        boxstyle="round,pad=0.0,rounding_size=0.02",
        linewidth=0, facecolor=PANEL, mutation_aspect=12 / 6.75))

    # Left accent bar
    ax.add_patch(plt.Rectangle((0.04, 0.06), 0.012, 0.88, color=accent))

    # --- Header: brand wordmark + category tag ---
    ax.text(0.085, 0.86, "ROKHAAN", color="white", fontsize=26,
            fontweight="bold", va="center")
    ax.text(0.085, 0.86, "ROKHAAN", color="white", fontsize=26,  # spacing trick
            fontweight="bold", va="center", alpha=0)
    # category pill
    ax.add_patch(FancyBboxPatch(
        (0.085, 0.745), 0.0085 * len(theme["label"]) + 0.04, 0.06,
        boxstyle="round,pad=0.012,rounding_size=0.03",
        linewidth=0, facecolor=accent, mutation_aspect=12 / 6.75))
    ax.text(0.105, 0.775, theme["label"], color=BG, fontsize=14,
            fontweight="bold", va="center")

    # --- Headline (wrapped, large) ---
    wrapped = "\n".join(textwrap.wrap(headline, width=32)[:4])
    ax.text(0.085, 0.45, wrapped, color="white", fontsize=33,
            fontweight="bold", va="center", linespacing=1.15)

    # --- Footer: source credit + handle ---
    ax.add_patch(plt.Rectangle((0.085, 0.155), 0.83, 0.004, color="#2a3038"))
    ax.text(0.085, 0.11, f"Source: {source}", color=MUTED, fontsize=15,
            va="center")
    ax.text(0.915, 0.11, "@Rokhaan", color=accent, fontsize=15,
            fontweight="bold", va="center", ha="right")

    fig.savefig(out_path, facecolor=BG)
    plt.close(fig)
    return out_path
