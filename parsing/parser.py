"""Define the ParseError exception used by the MapParser used to read map file."""

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
        """Initialize an empty parser with no zones or connections yet."""
        self.nb_drones: int = 0
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.seen_connections: set[tuple[str, str]] = set()
        self.start_zone: Zone | None = None
        self.end_zone: Zone | None = None

    def _parse_nb_drones(self, rest: str, line_number: int) -> None:
        """Read and parse the first line of the map file. Checks if the value
        of nb_drones is positive and a integer

        Args:
            rest: The result of the split of _parse_line
            line_number: The number of the line it's reading

        Raises:
            ParseError: if the number is not and integer, or is not positive
        """
        try:
            nb = int(rest)
        except ValueError:
            raise ParseError(line_number, f"invalid nb_drones value '{rest}'")
        if nb <= 0:
            raise ParseError(line_number, f"invalid nb_drones value '{rest}'")
        self.nb_drones = nb

    def _parse_line(self, line: str, line_number: int) -> None:
        """Determine the type of a line and dispatch it for parsing.

        Splits the line on the first ':' to separate the line type
        (e.g. 'hub', 'connection', 'nb_drones') from its content, then
        calls the appropriate parsing method for that type.

        Args:
            line: A single, already-cleaned line from the map file
            (comments stripped, no surrounding whitespace).
            line_number: The line number, used for error reporting.

        Raises:
            ParseError: If the line is missing a ':' separator, or if
                the line type is not one of the known types.
        """
        parts = line.split(":", 1)
        if len(parts) != 2:
            raise ParseError(line_number, "missing ':' separator")
        line_type = parts[0].strip()
        rest = parts[1].strip()
        if line_type not in {"nb_drones", "start_hub", "end_hub", "hub",
                             "connection"}:
            raise ParseError(line_number, f"unknown line type '{line_type}'")
        if line_type == "nb_drones":
            self._parse_nb_drones(rest, line_number)
        elif line_type == "start_hub":
            self._parse_zone(rest, line_number, is_start=True, is_end=False)
        elif line_type == "end_hub":
            self._parse_zone(rest, line_number, is_start=False, is_end=True)
        elif line_type == "hub":
            self._parse_zone(rest, line_number, is_start=False, is_end=False)
        elif line_type == "connection":
            self._parse_connection(rest, line_number)

    def parse(self, filepath: str) -> None:
        """Read and parse the map file at the given path.
        Args:
            filepath: Path to the map file to parse.

        Raises:
            ParseError: if any line in the file is invalid"""
        with open(filepath) as f:
            for line_number, raw_line in enumerate(f, start=1):
                line = raw_line.split("#")[0].strip()
                if not line:
                    continue
                self._parse_line(line, line_number)
        self._validate_final_state()
