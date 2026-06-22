"""
Generates a clean PNG 'headline card' for a news item.
Runs in the cloud (GitHub Actions) — no image software needed on your PC.
This is a DATA/text graphic, never a fake photo.
"""
import textwrap
import matplotlib
matplotlib.use("Agg")  # headless mode (no screen needed)
import matplotlib.pyplot as plt

# Colour theme per pillar (simple, recognisable branding)
PILLAR_THEME = {
    "global":            {"bg": "#0b1f3a", "accent": "#4da6ff", "label": "GLOBAL"},
    "us_foreign_policy": {"bg": "#1a1a2e", "accent": "#e94560", "label": "US FOREIGN POLICY"},
    "afghanistan":       {"bg": "#14342b", "accent": "#36c275", "label": "AFGHANISTAN"},
    "worldcup":          {"bg": "#2d1b00", "accent": "#ffb627", "label": "WORLD CUP 2026"},
    "afghan_cricket":    {"bg": "#11212d", "accent": "#06d6a0", "label": "AFGHAN CRICKET"},
}


def make_card(pillar, headline, source, out_path="card.png"):
    """Create a 1200x675 (16:9) news card image and save it to out_path."""
    theme = PILLAR_THEME.get(pillar, PILLAR_THEME["global"])

    fig = plt.figure(figsize=(12, 6.75), dpi=100)
    fig.patch.set_facecolor(theme["bg"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(theme["bg"])
    ax.axis("off")

    # Accent bar + category label (top)
    ax.add_patch(plt.Rectangle((0.05, 0.86), 0.02, 0.08,
                               color=theme["accent"], transform=ax.transAxes))
    ax.text(0.09, 0.88, theme["label"], color=theme["accent"],
            fontsize=20, fontweight="bold", transform=ax.transAxes)

    # Headline (wrapped so it fits)
    wrapped = "\n".join(textwrap.wrap(headline, width=34)[:4])
    ax.text(0.05, 0.55, wrapped, color="white", fontsize=34,
            fontweight="bold", va="center", transform=ax.transAxes)

    # Source credit (bottom) — credibility
    ax.text(0.05, 0.08, f"Source: {source}", color=theme["accent"],
            fontsize=18, transform=ax.transAxes)

    fig.savefig(out_path, facecolor=theme["bg"])
    plt.close(fig)
    return out_path
