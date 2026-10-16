"""Graphical representation of the simulation, drawn with pygame."""

import pygame

from network import Network
from zone import Zone

Color = tuple[int, int, int]
Point = tuple[float, float]

WIDTH = 1000
HEIGHT = 650
MARGIN = 90
TOP_MARGIN = 140
FPS = 60
TURN_DELAY_MS = 900
ZONE_RADIUS = 22
TERMINAL_RADIUS = 30
DRONE_HALF_SIZE = 8
DRONE_COLUMNS = 4
DRONE_SPACING_X = 40
DRONE_SPACING_Y = 24
LINK_BASE_WIDTH = 1
LINK_WIDTH_PER_CAPACITY = 2
LINK_MAX_WIDTH = 12

BACKGROUND: Color = (245, 245, 245)
OUTLINE: Color = (40, 40, 40)
LINK_COLOR: Color = (130, 130, 130)
DRONE_COLOR: Color = (35, 35, 45)
DEFAULT_ZONE_COLOR: Color = (200, 200, 200)

COLORS: dict[str, Color] = {
    "black": (30, 30, 30),
    "red": (220, 50, 47),
    "green": (60, 170, 80),
    "yellow": (240, 210, 50),
    "blue": (50, 110, 220),
    "magenta": (200, 60, 180),
    "cyan": (50, 190, 200),
    "white": (255, 255, 255),
    "gray": (150, 150, 150),
    "grey": (150, 150, 150),
    "orange": (245, 140, 30),
    "purple": (130, 70, 190),
    "brown": (140, 90, 50),
    "maroon": (128, 0, 0),
    "gold": (255, 200, 0),
}


class GraphView:
    """Window that draws the network and replays the simulation.

    The zones are placed from the coordinates of the map, the links are
    lines as thick as their capacity and the drones are dark diamonds
    with their id. The turns are replayed one at a time.

    Attributes:
        network: Network that is drawn.
        start: Name of the start zone.
        end: Name of the end zone.
        turns: Moves of every turn, as printed by the simulation.
        nb_drones: Number of drones of the simulation.
        turn_index: Number of turns already replayed.
        playing: True while the turns advance by themselves.
        positions: For each drone id, the zone it left and the zone it
            is going to. Both are equal when the drone is resting.
        links: Every link once, as (zone a, zone b, capacity).
        screen: Surface of the window.
        font: Font used for every text.
    """

    def __init__(self, network: Network, start: str, end: str,
                 nb_drones: int, turns: list[list[str]]) -> None:
        """Store the simulation and open the window.

        Args:
            network: Network to draw.
            start: Name of the start zone.
            end: Name of the end zone.
            nb_drones: Number of drones of the simulation.
            turns: Moves of every turn, as printed by the simulation.
        """
        self.network = network
        self.start = start
        self.end = end
        self.nb_drones = nb_drones
        self.turns = turns
        self.turn_index = 0
        self.playing = False
        self.positions = self.initial_positions()
        self.links = self.find_links()
        self.low_x, self.high_x, self.low_y, self.high_y = (
            self.find_bounds())
        pygame.init()
        pygame.display.set_caption("Fly-in")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.font = pygame.font.Font(None, 20)

    # ------------------------------------------------------------ setup

    def initial_positions(self) -> dict[str, tuple[str, str]]:
        """Put every drone in the start zone.

        Returns:
            The positions of the drones before the first turn.
        """
        return {f"D{number}": (self.start, self.start)
                for number in range(1, self.nb_drones + 1)}

    def find_links(self) -> list[tuple[str, str, int]]:
        """List every link of the network once.

        Returns:
            One (zone a, zone b, capacity) for each link, even though
            the network knows it from both of its ends.
        """
        seen: set[tuple[str, str]] = set()
        links: list[tuple[str, str, int]] = []
        for name, connections in self.network.neighbors.items():
            for connection in connections:
                other = connection.other(name)
                key = (min(name, other), max(name, other))
                if key in seen:
                    continue
                seen.add(key)
                links.append((key[0], key[1],
                              connection.max_link_capacity))
        return links

    def find_bounds(self) -> tuple[int, int, int, int]:
        """Find the smallest and largest coordinates of the map.

        Returns:
            The tuple (low x, high x, low y, high y).
        """
        xs = [zone.x for zone in self.network.zones.values()]
        ys = [zone.y for zone in self.network.zones.values()]
        return min(xs), max(xs), min(ys), max(ys)

    # ------------------------------------------------------- coordinates

    @staticmethod
    def to_pixel(value: int, low: int, high: int, first: int,
                 last: int) -> float:
        """Convert a map coordinate into a pixel of the window.

        Args:
            value: Coordinate of the zone on one axis.
            low: Smallest coordinate of the map on that axis.
            high: Largest coordinate of the map on that axis.
            first: Pixel where the smallest coordinate is drawn.
            last: Pixel where the largest coordinate is drawn.

        Returns:
            The pixel where the coordinate is drawn. If all the zones
            have the same coordinate, the middle between the two pixels.
        """
        if high == low:
            return (first + last) / 2
        fraction = (value - low) / (high - low)
        return first + fraction * (last - first)

    def zone_pixel(self, name: str) -> Point:
        """Find where the centre of a zone is drawn.

        Args:
            name: Name of the zone.

        Returns:
            The (x, y) pixel of the zone.
        """
        zone = self.network.zones[name]
        return (
            self.to_pixel(zone.x, self.low_x, self.high_x,
                          MARGIN, WIDTH - MARGIN),
            self.to_pixel(zone.y, self.low_y, self.high_y,
                          TOP_MARGIN, HEIGHT - MARGIN),
        )

    def drone_pixel(self, drone_id: str) -> Point:
        """Find where a drone is, before spreading it from the others.

        A resting drone is at the centre of its zone. A drone in the
        middle of a restricted flight is halfway along the link.

        Args:
            drone_id: Id of the drone, like "D1".

        Returns:
            The (x, y) pixel of the drone.
        """
        origin, destination = self.positions[drone_id]
        origin_x, origin_y = self.zone_pixel(origin)
        dest_x, dest_y = self.zone_pixel(destination)
        return (origin_x + dest_x) / 2, (origin_y + dest_y) / 2

    def drones_in(self, name: str) -> int:
        """Count the drones resting in a zone.

        Args:
            name: Name of the zone.

        Returns:
            How many drones are in that zone and not in flight.
        """
        return sum(1 for origin, destination in self.positions.values()
                   if origin == name and destination == name)

    # ------------------------------------------------------------ colors

    @staticmethod
    def zone_color(zone: Zone) -> Color:
        """Choose the colour of a zone.

        Args:
            zone: Zone to colour.

        Returns:
            The colour given by the map, or grey when the zone has no
            colour or the map uses a name that is not known.
        """
        if zone.color is None:
            return DEFAULT_ZONE_COLOR
        return COLORS.get(zone.color.lower(), DEFAULT_ZONE_COLOR)

    # ----------------------------------------------------------- replay

    def apply_turn(self, moves: list[str]) -> None:
        """Update the positions of the drones with the moves of a turn.

        A move like "D1-roof" puts the drone in "roof". A move like
        "D2-hub-roof" leaves it in flight from "hub" to "roof".

        Args:
            moves: Moves of one turn.
        """
        for move in moves:
            parts = move.split("-")
            if len(parts) == 3:
                self.positions[parts[0]] = (parts[1], parts[2])
            else:
                self.positions[parts[0]] = (parts[1], parts[1])

    def advance(self) -> None:
        """Replay the next turn. Does nothing after the last one."""
        if self.turn_index >= len(self.turns):
            self.playing = False
            return
        self.apply_turn(self.turns[self.turn_index])
        self.turn_index += 1

    def reset(self) -> None:
        """Go back to the situation before the first turn."""
        self.turn_index = 0
        self.playing = False
        self.positions = self.initial_positions()

    # ----------------------------------------------------------- drawing

    def draw_text(self, text: str, center: Point, color: Color) -> None:
        """Draw a text centred on a point.

        Args:
            text: Text to draw.
            center: Pixel where the text is centred.
            color: Colour of the text.
        """
        image = self.font.render(text, True, color)
        self.screen.blit(image, image.get_rect(center=center))

    def draw_link(self, first: str, second: str, capacity: int) -> None:
        """Draw a link as a line as thick as its capacity.

        Args:
            first: Name of one end of the link.
            second: Name of the other end of the link.
            capacity: Maximum number of drones on the link at once.
        """
        width = min(LINK_BASE_WIDTH + LINK_WIDTH_PER_CAPACITY * capacity,
                    LINK_MAX_WIDTH)
        pygame.draw.line(self.screen, LINK_COLOR,
                         self.zone_pixel(first), self.zone_pixel(second),
                         width)

    def draw_zone(self, name: str) -> None:
        """Draw a zone: a coloured circle, its name and its drones.

        The start and end zones are bigger. The number of resting
        drones is written inside the circle when there is any.

        Args:
            name: Name of the zone.
        """
        zone = self.network.zones[name]
        radius = ZONE_RADIUS
        if name in (self.start, self.end):
            radius = TERMINAL_RADIUS
        center = self.zone_pixel(name)
        pygame.draw.circle(self.screen, self.zone_color(zone), center,
                           radius)
        pygame.draw.circle(self.screen, OUTLINE, center, radius, 2)
        self.draw_text(name, (center[0], center[1] + radius + 12), OUTLINE)
        count = self.drones_in(name)
        if count > 0:
            self.draw_text(str(count), center, OUTLINE)

    def draw_drone(self, drone_id: str, center: Point) -> None:
        """Draw a drone as a dark diamond with its id beside it.

        Args:
            drone_id: Id of the drone, like "D1".
            center: Pixel where the diamond is centred.
        """
        x, y = center
        size = DRONE_HALF_SIZE
        points = [(x, y - size), (x + size, y),
                  (x, y + size), (x - size, y)]
        pygame.draw.polygon(self.screen, DRONE_COLOR, points)
        self.draw_text(drone_id, (x + size + 14, y), DRONE_COLOR)

    def draw_drones(self) -> None:
        """Draw every drone.

        Drones that would be on the same pixel are spread in rows above
        it, so none of them hides another.
        """
        placed: dict[Point, int] = {}
        for drone_id in self.positions:
            base = self.drone_pixel(drone_id)
            index = placed.get(base, 0)
            placed[base] = index + 1
            column = index % DRONE_COLUMNS
            row = index // DRONE_COLUMNS
            offset_x = (column - (DRONE_COLUMNS - 1) / 2) * DRONE_SPACING_X
            offset_y = -(TERMINAL_RADIUS + 14) - row * DRONE_SPACING_Y
            self.draw_drone(drone_id,
                            (base[0] + offset_x, base[1] + offset_y))

    def draw_hud(self) -> None:
        """Draw the turn counter and the keys at the top of the window."""
        state = "playing" if self.playing else "paused"
        if self.turn_index >= len(self.turns):
            state = "finished"
        text = (f"Turn {self.turn_index}/{len(self.turns)} ({state})   "
                "SPACE: next   P: play/pause   R: restart   ESC: quit")
        self.draw_text(text, (WIDTH / 2, 20), OUTLINE)

    def draw(self) -> None:
        """Draw the whole window and show it."""
        self.screen.fill(BACKGROUND)
        for first, second, capacity in self.links:
            self.draw_link(first, second, capacity)
        for name in self.network.zones:
            self.draw_zone(name)
        self.draw_drones()
        self.draw_hud()
        pygame.display.flip()

    # -------------------------------------------------------------- loop

    def handle_events(self) -> bool:
        """React to the window being closed and to the keys.

        Returns:
            False when the window must close, True otherwise.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key in (pygame.K_SPACE, pygame.K_RIGHT):
                self.advance()
            elif event.key == pygame.K_p:
                self.playing = not self.playing
            elif event.key == pygame.K_r:
                self.reset()
        return True

    def run(self) -> None:
        """Keep the window open until the user closes it."""
        clock = pygame.time.Clock()
        last_advance = pygame.time.get_ticks()
        running = True
        while running:
            running = self.handle_events()
            now = pygame.time.get_ticks()
            if self.playing and now - last_advance >= TURN_DELAY_MS:
                self.advance()
                last_advance = now
            self.draw()
            clock.tick(FPS)
        pygame.quit()
