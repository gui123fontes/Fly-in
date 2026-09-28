"""Define the ParseError exception used by the
MapParser used to read map file."""

from zone import Zone, ZoneType
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

    def _parse_connection(self, rest: str, line_number: int) -> None:
        """Parse a 'connection:' line and register a new Connection.

        Splits off an optional metadata block, extracts the two zone
        names, validates that both zones are already known, checks for
        duplicate connections (in either direction), and creates the
        resulting Connection.

        Args:
            rest: Everything after 'connection:' on the line, already
                stripped of surrounding whirtetspace.
            line_number: The line number, used for error reporting.

        Raises:
            ParseError: If the metadata block is malformed, if the line
                does not name exactly two zones, if either zone is
                unknown, or if this connection was already defined."""
        parts = rest.split("[", 1)
        max_link_capacity = 1
        if len(parts) == 1:
            connection_part = parts[0].strip()
            metadata_part = None
        else:
            connection_part = parts[0].strip()
            metadata_raw = parts[1].strip()
            if not metadata_raw.endswith("]"):
                raise ParseError(
                    line_number, "metadata block not closed with ']'"
                )
            metadata_part = metadata_raw[:-1]

        if metadata_part is not None:
            metadata = self._parse_metadata(metadata_part, line_number)
            for meta_key in metadata:
                if meta_key != "max_link_capacity":
                    raise ParseError(
                        line_number,
                        f"unknwon connection metadata '{meta_key}'")

            if "max_link_capacity" in metadata:
                raw = metadata["max_link_capacity"]
                try:
                    max_link_capacity = int(raw)
                except ValueError:
                    raise ParseError(
                        line_number, f"invalid max_link_capacity '{raw}'"
                    )
                if max_link_capacity <= 0:
                    raise ParseError(
                        line_number, f"invalid max_link_capacity '{raw}'"
                    )

        connection_zones = connection_part.split("-")
        if len(connection_zones) != 2:
            raise ParseError(line_number,
                             "connection zones must be exactly two")
        zone_a = connection_zones[0].strip()
        zone_b = connection_zones[1].strip()
        if zone_a not in self.zones:
            raise ParseError(line_number,
                             f"connection reference unknown zone '{zone_a}")
        if zone_b not in self.zones:
            raise ParseError(line_number,
                             f"connection references unknown zone '{zone_b}")
        key = (min(zone_a, zone_b), max(zone_a, zone_b))
        if key in self.seen_connections:
            raise ParseError(line_number,
                             f"duplicate connection {zone_a}-{zone_b}")
        self.seen_connections.add(key)
        connection = Connection(zone_a, zone_b, max_link_capacity)
        self.connections.append(connection)

    def _parse_zone(
            self,
            rest: str,
            line_number: int,
            is_start: bool,
            is_end: bool,
    ) -> None:
        """Parse a 'hub:', 'start_hub:' or 'end_hub:' line.

        Splits off an optional metadata block, reads the name and the
        integer coordinates, applies the metadata (zone type, color and
        max_drones) and registers the new Zone.

        Args:
            rest: Everything after the line type, already stripped.
            line_number: The line number, used for error reporting.
            is_start: True if the line is a 'start_hub:'.
            is_end: True if the line is an 'end_hub:'.

        Raises:
            ParseError: If the metadata block is malformed, the line
                does not have a name and two integer coordinates, the
                name is invalid or duplicated, a metadata value is
                invalid, or a second start/end zone is defined.
        """
        parts = rest.split("[", 1)
        zone_part = parts[0].strip()
        metadata: dict[str, str] = {}
        if len(parts) == 2:
            metadata_raw = parts[1].strip()
            if not metadata_raw.endswith("]"):
                raise ParseError(
                    line_number, "metadata block not closed with ']'"
                )
            metadata = self._parse_metadata(metadata_raw[:-1], line_number)

        fields = zone_part.split()
        if len(fields) != 3:
            raise ParseError(
                    line_number, "zone must be '<name> <x> <y>'"
            )
        name = fields[0]
        if "-" in name:
            raise ParseError(
                line_number, f"zone name '{name}' cannot contain '-'"
            )
        if name in self.zones:
            raise ParseError(line_number, f"duplicate zone '{name}'")
        try:
            x = int(fields[1])
            y = int(fields[2])
        except ValueError:
            raise ParseError(
                line_number,
                f"invalid coordinates '{fields[1]} {fields[2]}'"
            )

        zone_type = ZoneType.NORMAL
        color: str | None = None
        max_drones = 1
        for key, value in metadata.items():
            if key == "zone":
                try:
                    zone_type = ZoneType.from_str(value)
                except ValueError:
                    raise ParseError(
                        line_number, f"invalid zone type '{value}'"
                    )
            elif key == "color":
                color = value
            elif key == "max_drones":
                if is_start or is_end:
                    continue
                try:
                    max_drones = int(value)
                except ValueError:
                    raise ParseError(
                        line_number, f"invalid max_drones '{value}'"
                    )
                if max_drones <= 0:
                    raise ParseError(
                        line_number, f"invalid max_drones '{value}'"
                    )
            else:
                raise ParseError(
                    line_number, f"unknown zone metadata '{key}'"
                )

            zone = Zone(
                name, x, y, zone_type, color, max_drones, is_start, is_end
            )
            if is_start:
                if self.start_zone is not None:
                    raise ParseError(line_number, "duplicate start_hub")
                self.start_zone = zone
            if is_end:
                if self.end_zone is not None:
                    raise ParseError(line_number, "duplicate end_hub")
                self.end_zone = zone
            self.zones[name] = zone

    def _parse_metadata(
            self, metadata_part: str, line_number: int) -> dict[str, str]:
        """Parse a netadata block into a dictionary of key-value pairs.
        Splits the content of a '[...]' block (without the brackets) on
        whitespace to get individual 'key=value' tokens, theb splits each
        token on '=' to build the resulting dictionary.
        Args:
            metadata_part: The raw text between the square brackets,
                e.g. "zone=normal color=blue.
            line_number: The line number, used for error reporting

        Returns:
            A dictionary mapping each metadata key to its raw string value.
            Values are not yet converted or validated against expected types;
            callers are responsible for interpreting them.

        Raises:
            ParseError: If any token is not in the form 'key=value'.
        """
        metadata: dict[str, str] = {}
        tokens = metadata_part.split()
        for token in tokens:
            pair = token.split("=")
            if len(pair) != 2:
                raise ParseError(line_number, "invalid metadata")
            key = pair[0].strip()
            value = pair[1].strip()
            metadata[key] = value
        return metadata

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
