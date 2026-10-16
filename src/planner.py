"""Choice of the path followed by each drone."""

from network import Network
from pathfinder import PathFinder
from simulation import Simulation


class Planner:
    """Choose the path followed by every drone.

    Attributes:
        network: Network where the drones fly.
        finder: Path finder used to compare the candidate paths.
    """

    def __init__(self, network: Network, finder: PathFinder) -> None:
        """Store the network and the path finder.

        Args:
            network: Network with the zones and their connections.
            finder: Path finder built for the same network.
        """
        self.network = network
        self.finder = finder

    def assign_paths(self, candidates: list[list[str]],
                     nb_drones: int) -> list[list[str]]:
        """Choose a path for each drone, one drone at a time.

        For each drone, every candidate path is simulated together with
        the paths already chosen. The best one is the path with the
        fewest turns. If turns tie, the path with more priority zones
        wins, and then the shorter path.

        Args:
            candidates: Possible paths from the start to the end.
            nb_drones: Number of drones to plan.

        Returns:
            One path per drone.

        Raises:
            RuntimeError: If no candidate lets the drones reach the end.
        """
        chosen: list[list[str]] = []
        for _ in range(nb_drones):
            best: list[str] | None = None
            best_score = (0, 0, 0)
            for candidate in candidates:
                paths = chosen + [candidate]
                try:
                    turns = len(Simulation(self.network, paths).run())
                except RuntimeError:
                    continue
                score = (turns, self.finder.path_penalty(candidate),
                         len(candidate))
                if best is None or score < best_score:
                    best = candidate
                    best_score = score
            if best is None:
                raise RuntimeError(
                    "no path lets the drones reach the end zone")
            chosen.append(best)
        return chosen
