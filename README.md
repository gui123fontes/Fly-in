*This project has been created as part of the 42 curriculum by <gsilva-f>.*

# Fly-in

## Description

Fly-in is a drone routing simulator written in Python 3.10+. A map describes
a network of **zones** joined by **connections**. A fleet of drones starts in
the `start_hub` zone and must all reach the `end_hub` zone in as few
simulation turns as possible, while respecting:

- **Zone capacity** (`max_drones`, default 1): how many drones can be in
  a zone at the same time. The start and end zones have no limit.
- **Link capacity** (`max_link_capacity`, default 1): how many drones can use
  a connection during the same turn.
- **Zone types**: `normal` and `priority` zones cost 1 turn, `restricted`
  zones cost 2 turns, and `blocked` zones can never be entered.

The program reads a map file, computes a path for every drone, simulates the
movement turn by turn, prints one line per turn and can also show the
simulation in a window.

The project is fully object-oriented and fully typed (`flake8` and `mypy`
clean). No graph library (such as `networkx`) is used: the pathfinding is
implemented by hand.

## Instructions

### Requirements

- Python 3.10 or newer
- `pygame` (only needed for the graphical view), `flake8` and `mypy`

### Installation

```bash
make install
```

Create and activate a virtual environment first (`python3 -m venv .venv &&
source .venv/bin/activate`). `make install` installs the packages listed in
`requirements.txt` (`pygame`, `flake8`, `mypy`).

### Running

```bash
make run MAP=maps/test.txt                        # text output only
make run MAP=maps/test.txt ARGS=--stats           # also print the total turns
make run MAP=maps/test.txt ARGS=--gui             # also open the window
make run MAP=maps/test.txt ARGS="--gui --stats"   # both
```

or directly:

```bash
python3 src/main.py <map_file> [--gui] [--stats]
```

| Flag      | Effect                                                         |
|-----------|----------------------------------------------------------------|
| `--gui`   | Opens the pygame window after printing the turns.              |
| `--stats` | Prints `Total turns: N` on the error stream (stderr).          |

The statistics go to stderr so the standard output always keeps the exact
format required by the subject, even when it is redirected to a file.

### Other Makefile targets

| Target             | Description                                           |
|--------------------|-------------------------------------------------------|
| `make debug`       | Runs the program with Python's debugger.              |
| `make lint`        | Runs `flake8` and `mypy` with the required options.   |
| `make lint-strict` | Runs `flake8` and `mypy --strict`.                    |
| `make clean`       | Removes caches and temporary files.                   |

### Map format

```
nb_drones: 2
start_hub: hub 0 0 [color=green]
hub: roof1 3 4 [zone=restricted color=red]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
end_hub: goal 6 3 [color=yellow]
connection: hub-roof1
connection: hub-corridorA [max_link_capacity=2]
connection: roof1-goal
connection: corridorA-goal
```

The parser rejects invalid maps with an error that gives the **line number and
the cause**, for example:

```
Error: line 7: duplicate connection 'hub-roof1'
```

It checks, among other things: the first line, exactly one start and one end
zone, unique zone names, no dashes or spaces in names, connections only
between zones defined before, no duplicate connections (`a-b` is the same as
`b-a`), valid metadata syntax, valid zone types and positive integer
capacities.

### Project structure

```
src/
  main.py         Entry point and command line.
  parser.py       MapParser and ParseError: reads and validates a map.
  zone.py         Zone and ZoneType.
  connection.py   Connection between two zones.
  network.py      Network: zones plus their neighbours.
  pathfinder.py   PathFinder: Dijkstra and candidate paths.
  planner.py      Planner: chooses one path for each drone.
  drone.py        Drone: its path, its progress and its flight state.
  simulation.py   Simulation: runs the turns and applies every rule.
  renderer.py     TerminalRenderer: prints the turns, with colours.
  graph_view.py   GraphView: the pygame window.
maps/             Test maps (valid ones and maps/invalid/ for error cases).
```

## Algorithm and implementation strategy

The problem is solved in three separate stages, each one in its own class.

### 1. Shortest paths: `PathFinder`

`find_path` is a **Dijkstra** search written by hand (no priority-queue
library: the next node is taken with `min` over the pending zones, which is
enough for the size of the maps).

- The cost of a path is a tuple `(turns, penalty)`.
  - `turns` is the sum of the cost of every zone entered (1 or 2).
  - `penalty` is the number of zones entered that are **not** `priority`.
- Tuples are compared lexicographically, so the search first minimises the
  number of turns and, between paths with the **same** number of turns, it
  prefers the one that crosses more priority zones. This is how "priority
  zones should be prioritised" is applied without ever giving up speed.
- Blocked zones are never entered.
- If the end zone cannot be reached, a `ValueError` is raised and the program
  prints a clear error.

A single shortest path is not enough: with capacity 1, all drones on the same
path wait for each other. `candidate_paths` therefore returns **one candidate
path for every neighbour of the start zone**: the first step is forced to that
neighbour (the start zone is excluded from the rest of the search with the
`avoid` parameter) and the rest of the path is the shortest one. This gives
the planner genuinely different ways out of the start zone.

### 2. Choosing the paths: `Planner`

The planner assigns a path to the drones one by one (greedy strategy). For
each drone it tries every candidate path, **simulates** all the drones
assigned so far plus this one, and keeps the candidate that minimises, in
this order:

1. the total number of turns of the simulation,
2. the penalty of the path (more priority zones is better),
3. the length of the path.

Candidates that make the simulation fail are ignored. Because the choice is
made by running the real simulation, the planner automatically takes into
account zone capacities, link capacities and the 2-turn restricted zones,
without duplicating those rules.

### 3. Simulating the turns: `Simulation`

The simulation owns the state that changes during the run: how many drones are
in each zone (`occupancy`, which persists between turns) and how many drones
use each link (`link_usage`, which is reset at the start of every turn).

In every turn:

1. Drones that are **in flight** towards a restricted zone arrive first. Their
   destination was already reserved when they left.
2. The other drones are processed from the one that is **furthest along its
   path** to the one that is closest to the start, so a drone that leaves a
   zone frees the place for the one behind it in the same turn.
3. A drone moves only if the destination zone has room and the link has room.
   The start and end zones have unlimited room.
4. A move to a restricted zone takes two turns: the first turn is printed as
   `D<ID>-<connection>` (the drone is on the link) and the second as
   `D<ID>-<zone>` (it arrives). Drones in flight keep using the link capacity.

The run ends when every drone has reached the end zone. The number of turns
is the number of lines printed.

### Limits

The planner is a greedy heuristic: it is not proved to give the minimum
number of turns for every possible map.

## Performance

Reference targets of the subject, and the turns obtained:

| Map                        | Drones | Target | Turns |
|----------------------------|--------|--------|-------|
| Linear path                | 2      | ≤ 6    |   4   |
| Simple fork                | 4      | ≤ 8    |   6   |
| Basic capacity             | 4      | ≤ 6    |   4   |
| Dead end trap              | 5      | ≤ 12   |   8   |
| Circular loop              | 6      | ≤ 15   |   15  |
| Priority puzzle            | 5      | ≤ 12   |   7   |
| Maze nightmare             | 8      | ≤ 30   |   13  |
| Capacity hell              | 12     | ≤ 35   |   16  |
| Ultimate challenge         | 15     | ≤ 45   |   26  |
| The Impossible Dream (opt.)| 25     | < 45   |   67  |

Use `--stats` to see the total number of turns of any map.

## Visual representation

Two complementary views are available.

### Terminal output (default)

The turns are printed one per line, exactly as the subject asks, listing only
the drones that move. When the output is a terminal, every move is coloured
with the colour of its **destination zone** (the `color=` metadata of the
map), so it is easy to follow where each drone is going. When the output is
redirected to a file or a pipe, the colours are turned off automatically so
the text stays exactly in the required format.

### Graphical window (`--gui`)

A pygame window draws the network with the coordinates of the map:

- **Zones** are circles with the colour given by the map; the start and end
  zones are bigger. The name is written below and the **number of drones
  resting in the zone** is written inside the circle.
- **Connections** are lines whose thickness grows with `max_link_capacity`.
- **Drones** are dark diamonds with their id, drawn above their zone. A drone
  in flight to a restricted zone is drawn **halfway** along the connection.
- A header shows the current turn and the available keys.

| Key          | Action                               |
|--------------|--------------------------------------|
| `SPACE`/`→`  | Play the next turn                   |
| `P`          | Play / pause automatic playback      |
| `R`          | Restart from the first turn          |
| `ESC`        | Quit                                 |

This makes it easy to see where the drones queue, which paths are shared and
how the restricted zones delay a drone.

## Example

Input (`maps/example.txt`):

```
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: a 1 0
end_hub: goal 2 0 [color=gold]
connection: start-a
connection: a-goal
```

Command:

```bash
python3 src/main.py maps/example.txt --stats
```

Output:

```
D1-a
D1-goal D2-a
D2-goal
Total turns: 3
```

(the last line goes to stderr). `a` can hold only one drone, so D2 enters it in
the same turn in which D1 leaves it.

## Resources

### References

- E. W. Dijkstra, *A note on two problems in connexion with graphs*,
  Numerische Mathematik 1, 1959.
- T. Cormen et al., *Introduction to Algorithms*, chapter on single-source
  shortest paths.
- [Dijkstra's algorithm (Wikipedia)](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Python `typing` documentation](https://docs.python.org/3/library/typing.html)
- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [flake8](https://flake8.pycqa.org/) and [mypy](https://mypy.readthedocs.io/)
- [pygame documentation](https://www.pygame.org/docs/)

### Use of AI

Claude (Anthropic) was used during the project, mainly as a tutor:

- To discuss the design step by step (parser, network, pathfinding, simulation
  rules, turn order, capacities) and to understand the algorithms before
  writing them.
- To review code and explain `flake8` / `mypy` errors.
- To generate part of the graphical view (`graph_view.py`), the test maps and
  the first draft of this README.

All the generated code was read, tested with the subject maps and my own maps,
and adjusted before being kept.
