"""Shared presentation helpers (emojis, badges, status indicators).

Kept separate from pawpal_system.py so the domain logic stays presentation-free,
and imported by BOTH the CLI demo (main.py) and the Streamlit UI (app.py) so the
two interfaces format tasks consistently.
"""

# Color-dot badge per priority level, so importance reads at a glance.
PRIORITY_BADGE = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}

# Keyword -> emoji, so each task shows an icon for its type of care.
TYPE_ICONS = {
    "feed": "🍽️",
    "walk": "🚶",
    "med": "💊",
    "groom": "✂️",
    "brush": "🧼",
    "bath": "🛁",
    "play": "🎾",
    "vet": "🏥",
}


def type_icon(description: str) -> str:
    """Pick a task-type emoji from keywords in the description (🐾 fallback)."""
    text = description.lower()
    for keyword, icon in TYPE_ICONS.items():
        if keyword in text:
            return icon
    return "🐾"


def priority_badge(priority: str) -> str:
    """Return a color-dot badge for a priority level."""
    return PRIORITY_BADGE.get(priority, priority)


def status_icon(completed: bool) -> str:
    """Color-coded status indicator: done vs. pending."""
    return "✅ Done" if completed else "⏳ Pending"
