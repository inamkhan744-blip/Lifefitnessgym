'''utils.py
Utility functions shared across the gym‑app project.

This module now provides:
- `get_gym_name(gym_id)`: Return the display name of a gym.
- `get_user_stats(user_id)`: Return a dictionary with basic statistics for a user.
- `get_recent_activities(gym_id, limit=10)`: Return the most recent activity records for a gym.

All functions are defensive – they catch database errors and return sensible defaults so that the UI never crashes because of missing data.
'''

from __future__ import annotations

import logging
from typing import Any, Dict, List

# Assuming the project has a `database` module that provides ORM‑style helpers.
# If the actual API differs, adjust the import statements accordingly.
try:
    from database import (
        get_gym_by_id,
        get_user_by_id,
        get_activities_by_gym,
    )
except ImportError as e:
    # Log the problem – the functions will raise a clear error if used.
    logging.error("Database helper functions could not be imported: %s", e)
    raise

logger = logging.getLogger(__name__)


def get_gym_name(gym_id: int | str) -> str:
    """Return the human‑readable name of a gym.

    Parameters
    ----------
    gym_id: int | str
        The primary key of the gym in the database.

    Returns
    -------
    str
        The gym's name if found, otherwise a placeholder string.
    """
    try:
        gym = get_gym_by_id(gym_id)
        if gym is None:
            logger.warning("Gym with id %s not found.", gym_id)
            return "Unknown Gym"
        # The ORM object is expected to have a `name` attribute.
        return getattr(gym, "name", "Unnamed Gym")
    except Exception as exc:  # pragma: no cover – defensive catch‑all
        logger.exception("Error retrieving gym name for id %s", gym_id)
        return "Unknown Gym"


def get_user_stats(user_id: int | str) -> Dict[str, Any]:
    """Return a dictionary with basic statistics for a user.

    This helper is used by several dashboard pages. If the underlying
    database call fails, an empty stats dict is returned so the UI can still
    render.
    """
    try:
        user = get_user_by_id(user_id)
        if user is None:
            logger.warning("User with id %s not found.", user_id)
            return {}
        # Example stats – adapt to the actual schema.
        return {
            "total_sessions": getattr(user, "session_count", 0),
            "last_visit": getattr(user, "last_visit", None),
            "active_membership": getattr(user, "membership_active", False),
        }
    except Exception as exc:  # pragma: no cover
        logger.exception("Error retrieving stats for user %s", user_id)
        return {}


def get_recent_activities(gym_id: int | str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch the most recent activity records for a gym.

    Parameters
    ----------
    gym_id: int | str
        Identifier of the gym.
    limit: int, optional
        Maximum number of records to return (default 10).

    Returns
    -------
    list[dict]
        A list of activity dictionaries sorted by newest first.
    """
    try:
        activities = get_activities_by_gym(gym_id, limit=limit)
        # Convert ORM objects to plain dictionaries for Streamlit consumption.
        return [
            {
                "activity_id": getattr(a, "id", None),
                "member_name": getattr(a, "member_name", ""),
                "type": getattr(a, "type", ""),
                "timestamp": getattr(a, "timestamp", None),
            }
            for a in activities
        ]
    except Exception as exc:  # pragma: no cover
        logger.exception("Error fetching recent activities for gym %s", gym_id)
        return []

# Export the public API of this module – useful for `from utils import *`.
__all__ = [
    "get_gym_name",
    "get_user_stats",
    "get_recent_activities",
]
