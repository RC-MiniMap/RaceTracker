"""Live F1 driver rating engine.

Produces live race ratings on a 3-10 scale (baseline 6.5) using five scoring categories:
  - Pace: rolling lap time performance vs. field average
  - Racecraft: position changes (overtakes, defends, net gains/losses)
  - Execution: pit stops, tire strategy, restarts, clean driving
  - Position Impact: where driver is vs. grid position and expected position
  - Discipline: penalties, track limits, spins, contact, DNF

Updates every lap as the race progresses. First public rating shown after 3 laps.
Weights based on Sofascore / Sportmonks soccer rating models, adapted for F1.

Usage:
  ratings = calculate_live_ratings(race_data, current_lap, incidents_dict)
  # Returns: {"VER": 7.2, "HAM": 6.9, ...}
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

LOG = logging.getLogger(__name__)

# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class LapSnapshot:
    """Single lap record for a driver."""

    lap_number: int
    position: int
    lap_time: float  # seconds
    sector1: Optional[float] = None  # seconds
    sector2: Optional[float] = None
    sector3: Optional[float] = None
    compound: Optional[str] = None  # "Soft", "Medium", "Hard"
    pit_loss: float = 0.0  # seconds lost in pit (if pit lap)
    gap_to_leader: Optional[float] = None  # seconds
    status: str = "OK"  # OK, DNF, RET, NC, etc.


@dataclass
class DriverRaceData:
    """Complete race data for one driver."""

    driver_code: str
    grid_position: int
    laps: List[LapSnapshot] = field(default_factory=list)
    incidents: List[Dict[str, Any]] = field(
        default_factory=list
    )  # penalties, spins, etc.
    final_position: Optional[int] = None
    final_status: str = "OK"


@dataclass
class LiveRatingSnapshot:
    """Live rating for a driver at a specific lap."""

    driver_code: str
    current_lap: int
    pace_score: float  # -2 to +2
    racecraft_score: float  # -2 to +2
    execution_score: float  # -2 to +2
    position_score: float  # -2 to +2
    discipline_score: float  # -2 to +2
    overall_rating: float  # 3 to 10
    is_provisional: bool  # True if < 3 laps


# =============================================================================
# Constants & Configuration
# =============================================================================

# Baseline and scale
BASELINE_RATING = 6.5
MIN_RATING = 3.0
MAX_RATING = 10.0

# Minimum laps before first public rating (before that, show "provisional")
PROVISIONAL_THRESHOLD = 3

# Category weights (sum should equal ~1.0 for semantic meaning)
WEIGHT_PACE = 0.35
WEIGHT_RACECRAFT = 0.30
WEIGHT_EXECUTION = 0.20
WEIGHT_POSITION = 0.25
WEIGHT_DISCIPLINE = -0.40  # negative because we subtract it

# Pace scoring thresholds (rolling window comparisons)
PACE_WINDOW = 3  # use last 3 laps for rolling pace
PACE_EXCELLENT = -0.15  # lap 0.15s faster than field avg
PACE_GOOD = -0.05
PACE_POOR = 0.10

# Racecraft thresholds
OVERTAKE_GAIN = 0.12
SUCCESSFUL_DEFENSE = 0.08
LOST_POSITION_PACE = -0.06

# Execution thresholds
GOOD_PIT = 0.08
BAD_PIT = -0.12  # pit loss > 30s or bad restart
GOOD_RESTART = 0.10
BAD_RESTART = -0.10
STRONG_TIRE_MGMT = 0.15

# Position impact thresholds
PODIUM_FROM_LOWER = 0.20
EXPECTED_POSITION_MET = 0.05
UNDERPERFORMING = -0.08

# Discipline thresholds (all negative)
TRACK_LIMIT_WARNING = -0.08
MINOR_PENALTY = -0.25
MAJOR_PENALTY = -0.35
SPIN = -0.45
AVOIDABLE_CONTACT = -0.50
DNF_DRIVER_FAULT = -1.25

# Normalization range for category scores
NORM_MIN = -2.0
NORM_MAX = 2.0

# =============================================================================
# Scoring Functions
# =============================================================================


def _calculate_field_average_lap_time(
    all_drivers: List[DriverRaceData], lap_number: int
) -> float:
    """Calculate field average lap time for a specific lap."""
    times = []
    for driver in all_drivers:
        for snap in driver.laps:
            if snap.lap_number == lap_number and snap.status == "OK":
                times.append(snap.lap_time)
    return sum(times) / len(times) if times else 0.0


def _get_rolling_pace(
    driver: DriverRaceData, current_lap: int, window: int = 3
) -> Optional[float]:
    """Return average lap time over last N laps."""
    recent_laps = [snap for snap in driver.laps if snap.lap_number <= current_lap][
        -window:
    ]
    if not recent_laps:
        return None
    return sum(snap.lap_time for snap in recent_laps) / len(recent_laps)


def score_pace(
    driver: DriverRaceData,
    all_drivers: List[DriverRaceData],
    current_lap: int,
) -> float:
    """
    Score pace contribution (-2 to +2).

    Uses rolling average vs. field average. Excellent pace gets +2, poor gets -2.
    """
    driver_pace = _get_rolling_pace(driver, current_lap, window=PACE_WINDOW)
    field_avg = _calculate_field_average_lap_time(all_drivers, current_lap)

    if driver_pace is None or field_avg == 0:
        return 0.0

    pace_delta = driver_pace - field_avg  # negative = faster

    if pace_delta < PACE_EXCELLENT:
        return 2.0  # exceptional pace
    elif pace_delta < PACE_GOOD:
        return 1.0  # good pace
    elif pace_delta < PACE_POOR:
        return 0.0  # average pace
    else:
        return -1.5  # poor pace

    # Clamp to [-2, 2]
    return max(NORM_MIN, min(NORM_MAX, pace_delta * 10))


def score_racecraft(driver: DriverRaceData, current_lap: int) -> float:
    """
    Score racecraft contribution (-2 to +2).

    Based on position changes, overtakes, successful defenses, net position gain vs grid.
    """
    if not driver.laps:
        return 0.0

    recent_laps = [snap for snap in driver.laps if snap.lap_number <= current_lap]

    # Count position changes (net overtakes vs. defenses)
    overtakes = 0
    defenses = 0
    for i in range(1, len(recent_laps)):
        prev_pos = recent_laps[i - 1].position
        curr_pos = recent_laps[i].position
        if prev_pos > curr_pos:
            overtakes += 1
        elif prev_pos < curr_pos:
            defenses += 1

    # Net position change from grid
    grid_pos = driver.grid_position
    current_pos = recent_laps[-1].position if recent_laps else grid_pos
    position_gain = grid_pos - current_pos  # positive = gained places

    # Scoring formula
    racecraft = (
        (overtakes * OVERTAKE_GAIN)
        + (defenses * SUCCESSFUL_DEFENSE)
        + (position_gain * 0.05)
    )

    return max(NORM_MIN, min(NORM_MAX, racecraft))


def score_execution(driver: DriverRaceData, current_lap: int) -> float:
    """
    Score execution contribution (-2 to +2).

    Based on pit stop quality, tire management, restarts, clean driving.
    """
    execution = 0.0

    # Analyze pit stops (if any)
    pit_laps = [snap for snap in driver.laps if snap.pit_loss > 0]
    for pit_lap in pit_laps:
        if pit_lap.pit_loss < 25.0:
            execution += GOOD_PIT  # good pit stop
        elif pit_lap.pit_loss > 35.0:
            execution += BAD_PIT  # slow pit stop

    # Tire management (proxy: consistency in sector times, no sudden degradation)
    # Simple heuristic: if late-stint pace close to early-stint, good tire mgmt
    early_laps = [s for s in driver.laps if s.lap_number <= 5]
    late_laps = [s for s in driver.laps if s.lap_number > current_lap - 5]
    if early_laps and late_laps:
        early_pace = sum(s.lap_time for s in early_laps) / len(early_laps)
        late_pace = sum(s.lap_time for s in late_laps) / len(late_laps)
        if late_pace < early_pace + 2.0:  # pace held well
            execution += STRONG_TIRE_MGMT

    return max(NORM_MIN, min(NORM_MAX, execution))


def score_position_impact(
    driver: DriverRaceData,
    all_drivers: List[DriverRaceData],
    current_lap: int,
    total_laps: int,
) -> float:
    """
    Score position impact contribution (-2 to +2).

    Compares current position vs. grid position and expected position based on pace.
    Rewards leading, podium, grid gain, and penalizes underperformance.
    """
    if not driver.laps:
        return 0.0

    current_pos = driver.laps[-1].position
    grid_pos = driver.grid_position

    # Reward leading driver significantly
    if current_pos == 1:
        return 2.0  # Exceptional: leading the race

    # Reward podium finishes
    if current_pos <= 3:
        return 1.5  # Very good: in podium positions

    # Expected position: roughly sorted by grid (assumes little chaos)
    # For simplicity, expect position ~ grid_pos ± 3, but account for overtakes
    # Allow a wider range early in race (chaos), narrower later (grid order reasserts)
    lap_progress = current_lap / total_laps
    chaos_window = 5 if lap_progress < 0.25 else 3
    expected_pos = max(1, min(len(all_drivers), grid_pos + chaos_window))

    position_delta = expected_pos - current_pos  # positive = better than expected

    # Scoring: reward for beating grid position, penalize underperformance
    if position_delta >= 5:  # significantly ahead (e.g., P10 grid → P2)
        return 2.0
    elif position_delta >= 3:
        return 1.5
    elif position_delta >= 1:
        return 1.0
    elif position_delta > -1:
        return 0.0
    elif position_delta >= -2:
        return -0.5
    else:
        return -1.5

    return max(NORM_MIN, min(NORM_MAX, position_delta * 0.5))


def score_discipline(driver: DriverRaceData, current_lap: int) -> float:
    """
    Score discipline contribution (-2 to +2, where negative is penalizing).

    Based on penalties, track limits, spins, contact, DNF.
    """
    discipline = 0.0

    # Sum all incident penalties up to current lap
    for incident in driver.incidents:
        if incident.get("lap", 999) <= current_lap:
            incident_type = incident.get("type", "")
            if incident_type == "track_limit":
                discipline += TRACK_LIMIT_WARNING
            elif incident_type == "penalty_minor":
                discipline += MINOR_PENALTY
            elif incident_type == "penalty_major":
                discipline += MAJOR_PENALTY
            elif incident_type == "spin":
                discipline += SPIN
            elif incident_type == "contact":
                discipline += AVOIDABLE_CONTACT
            elif incident_type == "dnf_fault":
                discipline += DNF_DRIVER_FAULT

    return max(NORM_MIN, min(NORM_MAX, discipline))


# =============================================================================
# Event Detector
# =============================================================================


def detect_events(
    driver: DriverRaceData, current_lap: int, all_drivers: List[DriverRaceData]
) -> List[Dict[str, Any]]:
    """
    Detect and return events for a driver at current lap.

    Returns list of event dicts: {"type": "overtake", "lap": 5, "details": "..."}
    """
    events = []

    if len(driver.laps) < 2:
        return events

    prev_snap = driver.laps[-2]
    curr_snap = driver.laps[-1]

    # Overtake or position gain
    if prev_snap.position > curr_snap.position:
        events.append(
            {
                "type": "overtake",
                "lap": current_lap,
                "position_from": prev_snap.position,
                "position_to": curr_snap.position,
            }
        )

    # Position loss
    elif prev_snap.position < curr_snap.position:
        events.append(
            {
                "type": "position_loss",
                "lap": current_lap,
                "position_from": prev_snap.position,
                "position_to": curr_snap.position,
            }
        )

    # Pit stop detected (if pit_loss > 0)
    if curr_snap.pit_loss > 0:
        events.append(
            {
                "type": "pit_stop",
                "lap": current_lap,
                "pit_loss_seconds": curr_snap.pit_loss,
            }
        )

    # Possible spin/contact (large lap time spike + position loss)
    if len(driver.laps) >= 3:
        avg_recent = sum(s.lap_time for s in driver.laps[-3:-1]) / 2
        if (
            curr_snap.lap_time > avg_recent + 3.0
            and curr_snap.position > prev_snap.position
        ):
            events.append(
                {
                    "type": "possible_incident",
                    "lap": current_lap,
                    "lap_time_delta": curr_snap.lap_time - avg_recent,
                    "position_loss": curr_snap.position - prev_snap.position,
                }
            )

    return events


# =============================================================================
# Live Rating Calculation
# =============================================================================


def calculate_live_rating(
    driver: DriverRaceData,
    all_drivers: List[DriverRaceData],
    current_lap: int,
    total_laps: int,
) -> LiveRatingSnapshot:
    """
    Calculate live rating for a driver at a specific lap.

    Returns LiveRatingSnapshot with five category scores + overall 3-10 rating.
    """
    is_provisional = current_lap < PROVISIONAL_THRESHOLD

    # Score each category
    pace = score_pace(driver, all_drivers, current_lap)
    racecraft = score_racecraft(driver, current_lap)
    execution = score_execution(driver, current_lap)
    position = score_position_impact(driver, all_drivers, current_lap, total_laps)
    discipline = score_discipline(driver, current_lap)

    # Combine with weights: R = 6.5 + 0.35*P + 0.30*RC + 0.20*EX + 0.25*PI - 0.40*NE
    overall = (
        BASELINE_RATING
        + (WEIGHT_PACE * pace)
        + (WEIGHT_RACECRAFT * racecraft)
        + (WEIGHT_EXECUTION * execution)
        + (WEIGHT_POSITION * position)
        + (WEIGHT_DISCIPLINE * discipline)
    )

    # Clip to 3-10 range
    overall = max(MIN_RATING, min(MAX_RATING, overall))

    return LiveRatingSnapshot(
        driver_code=driver.driver_code,
        current_lap=current_lap,
        pace_score=pace,
        racecraft_score=racecraft,
        execution_score=execution,
        position_score=position,
        discipline_score=discipline,
        overall_rating=overall,
        is_provisional=is_provisional,
    )


def calculate_live_ratings(
    all_drivers: List[DriverRaceData], current_lap: int, total_laps: int
) -> Dict[str, LiveRatingSnapshot]:
    """
    Calculate live ratings for all drivers at a specific lap.

    Returns: {"VER": LiveRatingSnapshot(...), "HAM": LiveRatingSnapshot(...), ...}
    """
    ratings = {}
    for driver in all_drivers:
        rating = calculate_live_rating(driver, all_drivers, current_lap, total_laps)
        ratings[driver.driver_code] = rating
    return ratings


# =============================================================================
# Output Formatting (for API / frontend)
# =============================================================================


def ratings_to_json(ratings: Dict[str, LiveRatingSnapshot]) -> Dict[str, Any]:
    """Convert LiveRatingSnapshot dict to JSON-serializable dict."""
    return {
        driver_code: {
            "driver_code": snap.driver_code,
            "lap": snap.current_lap,
            "pace": round(snap.pace_score, 2),
            "racecraft": round(snap.racecraft_score, 2),
            "execution": round(snap.execution_score, 2),
            "position_impact": round(snap.position_score, 2),
            "discipline": round(snap.discipline_score, 2),
            "overall_rating": round(snap.overall_rating, 2),
            "is_provisional": snap.is_provisional,
        }
        for driver_code, snap in ratings.items()
    }


if __name__ == "__main__":
    # Quick test: create sample data and calculate ratings
    from datetime import datetime

    logging.basicConfig(level=logging.INFO)

    # Sample drivers
    ver = DriverRaceData(
        driver_code="VER",
        grid_position=1,
        laps=[
            LapSnapshot(lap_number=1, position=1, lap_time=94.5),
            LapSnapshot(lap_number=2, position=1, lap_time=94.2),
            LapSnapshot(lap_number=3, position=1, lap_time=93.9),
        ],
    )
    ham = DriverRaceData(
        driver_code="HAM",
        grid_position=2,
        laps=[
            LapSnapshot(lap_number=1, position=2, lap_time=94.7),
            LapSnapshot(lap_number=2, position=2, lap_time=94.8),
            LapSnapshot(lap_number=3, position=2, lap_time=94.5),
        ],
    )

    all_drivers = [ver, ham]

    # Calculate ratings at lap 3
    ratings = calculate_live_ratings(all_drivers, current_lap=3, total_laps=57)
    json_out = ratings_to_json(ratings)

    import json

    print(json.dumps(json_out, indent=2))
