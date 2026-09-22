from enum import Enum


class ZoneType(Enum):
    """The type of a zone, which determines movement cost and accessibility"""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @classmethod
    def from_str(cls, value: str) -> "ZoneType":
        """Convert a raw string into a ZoneType.
        Args:
            value: The raw string read from the map file (e.g. "restricted").

        Returns:
            The matching ZoneType member.

        Raises:
            ValueError: If value does not match any known zone type.
        """
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"invalid zone type '{value}'")


class Zone:

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: str | None = None,
        max_drones: int = 1,
        is_start: bool = False,
        is_end: bool = False,
    ) -> None:
        """Initialize a Zone.
        Args:
            name: Unique name of the zone (no dashes or spaces).
            x: Integer x-coordinate.
            y: Integer y-coordinate.
            zone_type: The type of this zone.
            color: Optional color string.
            max_drones: Requested capacity from the map file.
            is_start: True if this zone is the start_hub.
            is_end: True if this zone is the end_hub.
        """
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.is_start = is_start
        self.is_end = is_end
        self.max_drones = max_drones if not (is_start or is_end) else None

    def has_unlimited_capacity(self) -> bool:
        """Return True if this zone has no occupancy limit (start or end)."""
        return self.max_drones is None

    def is_acessible(self) -> bool:
        """Return True if drones are allowed to enter this zone at all."""
        return self.zone_type is not ZoneType.BLOCKED

    def movement_cost(self) -> int:
        """Return the number of turns required to move into this zone."""
        if self.zone_type is ZoneType.RESTRICTED:
            return 2
        return 1

    def __repr__(self) -> str:
        return (
            f"Zone(name={self.name!r}, x={self.x}, y={self.y}, "
            f"type={self.zone_type.value}, max_drones={self.max_drones}"
        )
