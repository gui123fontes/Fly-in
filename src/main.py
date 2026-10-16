"""Entry point of the Fly-in drone simulation."""

import sys
from parser import MapParser, ParseError
from network import Network
from pathfinder import PathFinder
from planner import Planner
from simulation import Simulation
from renderer import TerminalRenderer


def main() -> None:
    """Read the map, simulate the drones and print every turn."""
    parser = MapParser()
    args = sys.argv[1:]
    gui = "--gui" in args
    stats = "--stats" in args
    map_args = [arg for arg in args if arg not in ("--gui", "--stats")]
    if len(map_args) != 1:
        print("usage: python3 src/main.py <map_file> [--gui] [--stats]",
              file=sys.stderr)
        sys.exit(1)
    try:
        parser.parse(map_args[0])
        assert parser.start_zone is not None
        assert parser.end_zone is not None
        network = Network(parser.zones, parser.connections)
        finder = PathFinder(network)
        candidates = finder.candidate_paths(parser.start_zone.name,
                                            parser.end_zone.name)
        planner = Planner(network, finder)
        paths = planner.assign_paths(candidates, parser.nb_drones)
        turns = Simulation(network, paths).run()
    except (ParseError, OSError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    renderer = TerminalRenderer(network.zones)
    renderer.render(turns)
    if stats:
        print(f"Total turns: {len(turns)}", file=sys.stderr)
    if gui:
        from graph_view import GraphView
        view = GraphView(network, parser.start_zone.name,
                         parser.end_zone.name, parser.nb_drones, turns)
        view.run()


if __name__ == "__main__":
    main()
