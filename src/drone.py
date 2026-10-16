"""Define the Drone class, one drone following a fixed path."""


class Drone:
    """A drone that follows a path of zones, one step at a time.

    Attributes:
        drone_id: Number that identifies the drone (D1, D2, ...).
        path: Names of the zones the drone will visit, in order.
        step: Index in 'path' of the zone where the drone is.
        in_transit_to: Zone the drone is travelling to when it is
            in the middle of a restricted move, otherwise None.
    """

    def __init__(self, drone_id: int, path: list[str]) -> None:
        """Create a drone at the start of its path.

        Args:
            drone_id: Number that identifies the drone.
            path: Names of the zone to visit, from start to end.
        """
        self.drone_id = drone_id
        self.path = path
        self.step = 0
        self.in_transit_to: str | None = None

    def __repr__(self) -> str:
        """Return a readable description of the drone."""
        return (f"Drone(id={self.drone_id}, step={self.step}, "
                f"in_transit_to={self.in_transit_to})")
