"""Turn-by-turn simulation of the drones."""

from connection import Connection
from drone import Drone
from network import Network
from zone import Zone, ZoneType


class Simulation:
    """Simulate drones following fixed paths through a network.

    Attributes:
        network: Network where the drones fly.
        drones: Drones taking part in the simulation.
        occupancy: Number of drones in each zone.
        link_usage: Number of drones using each connection this turn.
    """

    def __init__(self, network: Network,
                 paths: list[list[str]]) -> None:
        """Place every drone in the start zone.

        Args:
            network: Network with the zones and their connections.
            paths: One path per drone, all starting in the same zone.
        """
        self.network = network
        self.drones = [Drone(number, paths[number - 1])
                       for number in range(1, len(paths) + 1)]
        self.occupancy: dict[str, int] = {paths[0][0]: len(paths)}
        self.link_usage: dict[tuple[str, str], int] = {}

    def run(self) -> list[list[str]]:
        """Run the simulation until every drone is done.

        Returns:
            The moves of each turn, as strings like "D1-corridorA".

        Raises:
            RuntimeError: If no drone can move in a turn.
        """
        turns: list[list[str]] = []
        while not all(self.is_done(drone) for drone in self.drones):
            self.link_usage = {}
            moves: list[str] = []
            busy: set[int] = set()
            for drone in self.drones:
                if drone.in_transit_to is None:
                    continue
                destination = drone.in_transit_to
                current = drone.path[drone.step]
                connection = self.find_connection(current, destination)
                key = self.link_key(connection)
                self.link_usage[key] = self.link_usage.get(key, 0) + 1
                self.finish_move(drone)
                busy.add(drone.drone_id)
                moves.append(f"D{drone.drone_id}-{destination}")
            for drone in sorted(self.drones, key=lambda d: d.step,
                                reverse=True):
                if drone.drone_id in busy or self.is_done(drone):
                    continue
                if not self.can_move(drone):
                    continue
                current = drone.path[drone.step]
                target = drone.path[drone.step + 1]
                self.start_move(drone)
                if drone.in_transit_to is None:
                    moves.append(f"D{drone.drone_id}-{target}")
                else:
                    moves.append(f"D{drone.drone_id}-{current}-{target}")
            if not moves:
                raise RuntimeError("simulation is stuck: no drone can move")
            turns.append(moves)
        return turns

    def zone_has_room(self, zone: Zone) -> bool:
        """Tell if a zone can receive one more drone.

        Args:
            zone: Zone the drone wants to enter.

        Returns:
            True if the zone has no limit or is not full.
        """
        if zone.max_drones is None:
            return True
        return self.occupancy.get(zone.name, 0) < zone.max_drones

    def link_has_room(self, connection: Connection) -> bool:
        """Tell if a connection can carry one more drone this turn.

        Args:
            connection: Connection the drone wants to use.

        Returns:
            True if the connection is not at its capacity.
        """
        used = self.link_usage.get(self.link_key(connection), 0)
        return used < connection.max_link_capacity

    def find_connection(self, current: str, next_zone: str) -> Connection:
        """Find the connection between two neighbouring zones.

        Args:
            current: Name of the zone where the drone is.
            next_zone: Name of the zone the drone goes to.

        Returns:
            The connection linking the two zones.

        Raises:
            ValueError: If the zones are not connected.
        """
        for connection in self.network.neighbors[current]:
            if connection.other(current) == next_zone:
                return connection
        raise ValueError(f"no connection between '{current}' "
                         f"and '{next_zone}'")

    def can_move(self, drone: Drone) -> bool:
        """Tell if a drone can start its next move this turn.

        Args:
            drone: Drone that waits in a zone.

        Returns:
            True if the next zone and the connection have room.
        """
        current = drone.path[drone.step]
        target = drone.path[drone.step + 1]
        connection = self.find_connection(current, target)
        zone = self.network.zones[target]
        return self.zone_has_room(zone) and self.link_has_room(connection)

    def start_move(self, drone: Drone) -> None:
        """Start the next move of a drone and update the counters.

        A move to a restricted zone takes two turns: the drone is left
        in transit and the destination is reserved at once.

        Args:
            drone: Drone that waits in a zone.
        """
        current = drone.path[drone.step]
        target = drone.path[drone.step + 1]
        connection = self.find_connection(current, target)
        key = self.link_key(connection)
        self.occupancy[current] -= 1
        self.occupancy[target] = self.occupancy.get(target, 0) + 1
        self.link_usage[key] = self.link_usage.get(key, 0) + 1
        if self.network.zones[target].zone_type == ZoneType.RESTRICTED:
            drone.in_transit_to = target
        else:
            drone.step += 1

    @staticmethod
    def link_key(connection: Connection) -> tuple[str, str]:
        """Build a key that does not depend on the direction.

        Args:
            connection: Connection to identify.

        Returns:
            The two zone names in alphabetical order.
        """
        return (min(connection.zone_a, connection.zone_b),
                max(connection.zone_a, connection.zone_b))

    @staticmethod
    def finish_move(drone: Drone) -> None:
        """Finish the move of a drone that was in transit.

        Args:
            drone: Drone that arrives at its destination.
        """
        drone.step += 1
        drone.in_transit_to = None

    @staticmethod
    def is_done(drone: Drone) -> bool:
        """Tell if a drone reached the end of its path.

        Args:
            drone: Drone to check.

        Returns:
            True if the drone is in the last zone of its path.
        """
        return drone.step == len(drone.path) - 1
