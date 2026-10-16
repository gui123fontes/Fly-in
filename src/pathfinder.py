"""Pathfinding over a network of zones."""

from network import Network
from zone import ZoneType


class PathFinder:
    """Find paths between the zones of a network.

    Attributes:
        network: Network where the paths are searched.
    """

    def __init__(self, network: Network) -> None:
        """Store the network used by every search.

        Args:
            network: Network with the zones and their neighbours.
        """
        self.network = network

    def find_path(self, start: str, end: str,
                  avoid: set[str] | None = None) -> list[str]:
        """Find the cheapest path between two zones.

        The cost of a path is a pair (turns, penalty). Paths are compared
        by turns first. If two paths take the same number of turns, the
        one that goes through more priority zones is chosen. The penalty
        counts the zones that are not priority, so a lower penalty is
        better.

        Args:
            start: Name of the zone where the path begins.
            end: Name of the zone where the path ends.
            avoid: Names of zones the path must not enter.

        Returns:
            The zone names from start to end, both included.

        Raises:
            ValueError: If there is no path from start to end.
        """
        if avoid is None:
            avoid = set()
        cost: dict[str, tuple[int, int]] = {start: (0, 0)}
        came_from: dict[str, str] = {}
        pending: list[str] = [start]

        while pending:
            current = min(pending, key=lambda name: cost[name])
            if current == end:
                break
            pending.remove(current)

            for connection in self.network.neighbors[current]:
                neighbor = connection.other(current)
                if neighbor in avoid:
                    continue
                zone_type = self.network.zones[neighbor].zone_type
                turns = 1
                if zone_type == ZoneType.RESTRICTED:
                    turns = 2
                penalty = 1
                if zone_type == ZoneType.PRIORITY:
                    penalty = 0
                new_cost = (cost[current][0] + turns,
                            cost[current][1] + penalty)
                if neighbor not in cost or new_cost < cost[neighbor]:
                    cost[neighbor] = new_cost
                    came_from[neighbor] = current
                    if neighbor not in pending:
                        pending.append(neighbor)

        if end not in cost:
            raise ValueError(f"no path from '{start}' to '{end}'")

        path = [end]
        while path[-1] != start:
            path.append(came_from[path[-1]])
        path.reverse()
        return path

    def candidate_paths(self, start: str, end: str) -> list[list[str]]:
        """Find one path for each link that leaves the start zone.

        Args:
            start: Name of the zone where the drones start.
            end: Name of the zone where the drones must arrive.

        Returns:
            The cheapest path found through each neighbour of the start.
        """
        paths: list[list[str]] = []
        for connection in self.network.neighbors[start]:
            neighbor = connection.other(start)
            try:
                rest = self.find_path(neighbor, end, avoid={start})
            except ValueError:
                continue
            paths.append([start] + rest)
        return paths

    def path_penalty(self, path: list[str]) -> int:
        """Count the zones of a path that are not priority zones.

        Args:
            path: Zone names from start to end.

        Returns:
            How many zones after the start are not priority zones.
        """
        penalty = 0
        for name in path[1:]:
            if self.network.zones[name].zone_type != ZoneType.PRIORITY:
                penalty += 1
        return penalty
