"""Colored terminal output of the simulation."""


import sys
from zone import Zone


RESET = "\033[0m"


class TerminalRenderer:
    """Print the turns of a simulation, with colors when possible.

    Colors are only used when the output is a terminal, so redirecting
    the output to a file keeps the plain format of the subject.

    Attributes:
        zones: Zones of the network, by name.
        used_color: Whether the output uses ANSI colors
    """

    CODES = {
        "black": "30", "red": "31", "green": "32", "yellow": "33",
        "blue": "34", "magenta": "35", "cyan": "36", "white": "37",
        "gray": "90", "orange": "38;5;208", "purple": "38;5;93",
    }

    def __init__(self, zones: dict[str, Zone]) -> None:
        """Store the zones and check if the output is a terminal.

        Args:
            zones: Zones of the network, by name.
        """
        self.zones = zones
        self.use_color = sys.stdout.isatty()

    def paint(self, text: str, color: str | None) -> str:
        """Color a text with an ANSI code, if colors are enabled.

        Args:
            text: Text to color.
            color: Name of the color, or None for no color.

        Returns:
            The colored text, or the same text if there is no color to
            use or the color is unknown.
        """
        code = self.CODES.get(color) if color else None
        if not self.use_color or code is None:
            return text
        return f"\033[{code}m{text}{RESET}"

    def format_move(self, move: str) -> str:
        """Color a move with the color of its destination zone.

        Args:
            move: Move like "D1-corridorA" or "D2-hub-roof1".

        Returns:
            The move, colored when its destination has a color.
        """
        destination = move.split("-")[-1]
        return self.paint(move, self.zones[destination].color)

    def render(self, turns: list[list[str]]) -> None:
        """Print one line for each turn.

        Args:
            turns: The moves of each turn.
        """
        for moves in turns:
            print(" ".join(self.format_move(move) for move in moves))
