class Connection:
    """A bidirectional link between two zones in the drone network.

    Attributes:
        zone_a: Name of one endpoint zone.
        zone_b: Name of the other endpoint zone.
        max_link_capacity: Maximum number of drones that can traverse
            this connection simultaneously.
    """
    def __init__(
            self, zone_a: str, zone_b: str, max_link_capacity: int = 1
    ) -> None:
        """Initialize a connection.
        Args:
            zone_a: name of the first zone
            zone_b: name of the second zone
            max_link_capacity: Maximum number of drones that can traverse
                this connection simultaneously. One by default
        """
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity

    def involves(self, name: str) -> bool:
        """Check whether this connection includes the given zone.

        Args:
            name: The zone name to check.

        Returns:
            True if the zone is one of the two endpoints of this connection.
        """
        return name in (self.zone_a, self.zone_b)

    def other(self, name: str) -> str:
        """Return the name of the zone on the other end of this connection.

        Args:
            name: The name of one endpoint zone.

        Returns:
            The name of the opposite endpoint zone.
        """
        return self.zone_b if name == self.zone_a else self.zone_a

    def __repr__(self) -> str:
        return (
            f"Connection(zone_a={self.zone_a!r}, zone_b={self.zone_b!r}, "
            f"max_link_capacity={self.max_link_capacity})"
        )
