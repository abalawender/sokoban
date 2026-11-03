# sokoban

A small Sokoban solver. Given a level file, it finds a solution with a
minimal number of pushes and prints the full player path.

## Usage

    python3 sokoban.py <level-file>

Example:

    python3 sokoban.py microban_83

Output: number of pushes/moves, the move string (`U`/`D`/`L`/`R`), and the
board rendered after every push.

## Level format

Standard Sokoban characters (same scheme as
[Racso/fzero-apps](https://github.com/Racso/fzero-apps/blob/main/sokoban/scripts/level.c)
`sokoban/scripts/level.c`):

| char | meaning          |
|------|------------------|
| `#`  | wall             |
| ` `  | floor            |
| `.`  | target           |
| `@`  | player           |
| `+`  | player on target |
| `$`  | crate            |
| `*`  | crate on target  |

## How it works

BFS over crate configurations, branching only on pushes (player movement
within a configuration is a quick inner BFS), with dead-square pruning.
Since every edge is one push, the first solution found is minimal in
pushes.

## Rendering

Single-width unicode glyphs: `▒` wall, `□` target, `■` crate, `▣` crate on
target, `☺`/`☻` player (on target).
