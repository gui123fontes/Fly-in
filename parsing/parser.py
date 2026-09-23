"""Define the ParseError exception used by the map parser."""

from zone import Zone
from connection import Connection


class ParseError(Exception):
    """Class that shows the line where the error occurred
    and the respective message
    """

    def __init__(self, line_number: int, message: str) -> None:
        """Initialize the error line and error message
        Args:
            line_number: The line number where the error occured
            message: The error message the user sees when the parsing fails
        """
        self.line_number = line_number
        self.message = message
        super().__init__(f"Line {line_number}: {message}")


class MapParser:
    """Does the parsing of all the given arguments"""

    def __init__(self) -> None:
        self.nb_drones: int = 0
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.seen_connections: set[tuple[str, str]] = set()
        self.start_zone: Zone | None = None
        self.end_zone: Zone | None = None

    def parse(self, filepath: str) -> None:
        with open(filepath) as f:
            for line_number, raw_line in enumerate(f, start=1):
                line = raw_line.split("#")[0].strip()
                if not line:
                    continue
                