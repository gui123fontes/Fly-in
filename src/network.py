"""Define the Network class, an index of which connections touch each zone."""

from zone import Zone, ZoneType
from connection import Connection


class Network:
    """The drone networkm indexed by zone.

    Attributes:
        zones: All zones, by name.
        neighbors: For each zone name, the connections that can be used
            to leave that zone. Connections touching a blocked zone are
            left out.
    """
    def __init__(
            self, zones: dict[str, Zone], connections: list[Connection]
    ) -> None:
        """Build the index of connections for every zone.

        Args:
            zones: All zones read from the map, by name.
            connections: All connections read from the map.
        """
        self.zones = zones
        self.neighbors: dict[str, list[Connection]] = {}
        for name in zones:
            self.neighbors[name] = []
        for connection in connections:
            if (zones[connection.zone_a].zone_type == ZoneType.BLOCKED
                    or zones[connection.zone_b].zone_type == ZoneType.BLOCKED):
                continue
            self.neighbors[connection.zone_a].append(connection)
            self.neighbors[connection.zone_b].append(connection)
