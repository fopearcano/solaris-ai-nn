"""Seasonality -- slow drift over simulated days/weeks/months.

Seasons advance on a fixed interval and shift the *dominant* stimulus
character, the absence/novelty rates, the danger/reward balance, and the
delayed-consequence timing. Changes are deterministic with the seed and
deliberately slow, so a report can ask the right long-horizon question:
did the system adapt to the shift, or only react to it?
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

# season name -> multipliers (absence, novelty, danger, reward,
#                             delay_steps) applied on top of the regime.
_SEASON_PROFILES: Dict[str, Tuple[float, float, float, float, int]] = {
    "spring": (0.8, 1.4, 0.8, 1.3, 3),    # novelty rich, mild
    "summer": (0.6, 1.0, 1.2, 1.2, 4),    # active, more danger/reward
    "autumn": (1.0, 0.8, 1.0, 0.8, 6),    # winding down, slower feedback
    "winter": (1.5, 0.5, 0.7, 0.6, 8),    # sparse, quiet, slow
}

SEASON_ORDER = ("spring", "summer", "autumn", "winter")


@dataclass
class SeasonalityModel:
    """Deterministic slow drift across seasons."""

    shift_interval: int = 200
    current_season: str = field(default="spring", init=False)
    season_index: int = field(default=0, init=False)
    shifts: List[Dict[str, Any]] = field(default_factory=list)

    def season_at(self, step: int) -> str:
        if self.shift_interval <= 0:
            return SEASON_ORDER[0]
        index = (step // self.shift_interval) % len(SEASON_ORDER)
        return SEASON_ORDER[index]

    def update(self, step: int) -> Tuple[str, bool]:
        """(season, shifted_this_step)."""
        season = self.season_at(step)
        shifted = season != self.current_season
        if shifted:
            self.shifts.append({
                "step": step, "from": self.current_season,
                "to": season})
            self.shifts = self.shifts[-100:]
            self.current_season = season
            self.season_index = SEASON_ORDER.index(season)
        return (season, shifted)

    def profile(self, season: str = "") -> Dict[str, float]:
        season = season or self.current_season
        absence, novelty, danger, reward, delay = _SEASON_PROFILES[
            season]
        return {"absence_mult": absence, "novelty_mult": novelty,
                "danger_mult": danger, "reward_mult": reward,
                "delay_steps": float(delay)}

    def snapshot(self) -> Dict[str, Any]:
        return {
            "current_season": self.current_season,
            "shift_interval": self.shift_interval,
            "shift_count": len(self.shifts),
            "profile": self.profile(),
            "recent_shifts": self.shifts[-5:],
            "note": "seasonal drift is slow and deterministic; reports "
                    "show whether the system adapts",
        }
