import sys
from collections import deque

# (row delta, col delta, move character) for each direction
MOVES = ((-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R'))


# level file character scheme, same as Racso/fzero-apps sokoban/scripts/level.c:
#   '#' wall   ' ' floor   '.' target   '@' player   '+' player on target
#   '$' crate  '*' crate on target
def load_level(path):
    with open(path) as f:
        rows = f.read().splitlines()
    # pad ragged rows with floor (like level.c's zero-initialized board) and add
    # a 1-cell wall border so indexing never goes out of range; render() strips
    # the border again
    width = max(len(row) for row in rows)
    grid = ([['#'] * (width + 2)]
            + [['#'] + list(row) + [' '] * (width + 1 - len(row)) for row in rows]
            + [['#'] * (width + 2)])

    players = []
    crates = []
    targets = []
    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            if cell in '# ':
                continue
            if cell == '.':
                targets.append((i, j))
            elif cell == '@':
                players.append((i, j))
            elif cell == '+':
                players.append((i, j))
                targets.append((i, j))
            elif cell == '$':
                crates.append((i, j))
            elif cell == '*':
                crates.append((i, j))
                targets.append((i, j))
            else:
                raise ValueError(f"unknown level character {cell!r} at {(i, j)}")
            row[j] = ' '

    assert len(players) == 1, f"expected exactly one player, found {len(players)}"
    return grid, players[0], crates, targets


def alive_squares(grid, targets):
    """Cells from which a crate can still be pushed onto some target."""
    alive = set(targets)
    queue = deque(targets)
    while queue:
        tx, ty = queue.popleft()
        for mx, my, _ in MOVES:
            # a crate at src pushed to (tx, ty) needs the player at 'behind'
            src = (tx - mx, ty - my)
            behind = (tx - 2 * mx, ty - 2 * my)
            if (grid[src[0]][src[1]] != '#' and grid[behind[0]][behind[1]] != '#'
                    and src not in alive):
                alive.add(src)
                queue.append(src)
    return alive


def reachable_cells(grid, crates, start):
    """Cells the player can reach with the crates fixed in place."""
    reach = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for mx, my, _ in MOVES:
            nxt = (x + mx, y + my)
            if grid[nxt[0]][nxt[1]] == '#' or nxt in crates or nxt in reach:
                continue
            reach.add(nxt)
            queue.append(nxt)
    return reach


def walk_path(grid, crates, src, dst):
    """Shortest player move string from src to dst with the crates fixed."""
    if src == dst:
        return ''
    came_from = {src: None}
    queue = deque([src])
    while queue:
        x, y = queue.popleft()
        for mx, my, ch in MOVES:
            nxt = (x + mx, y + my)
            if grid[nxt[0]][nxt[1]] == '#' or nxt in crates or nxt in came_from:
                continue
            came_from[nxt] = (x, y, ch)
            if nxt == dst:
                moves = []
                cur = dst
                while came_from[cur] is not None:
                    px, py, ch = came_from[cur]
                    moves.append(ch)
                    cur = (px, py)
                return ''.join(reversed(moves))
            queue.append(nxt)
    return None


def solve(grid, player, crates, targets):
    """BFS over crate configurations, branching only on pushes.

    Every edge is one push, so the first solution found has a minimal
    number of pushes. Returns (push_chain, moves), or None if unsolvable.
    Each push_chain entry is (prev_config, player_pos_in_prev, stand_cell, move).
    """
    target_set = frozenset(targets)
    start = frozenset(crates)
    if start == target_set:
        return [], ''
    alive = alive_squares(grid, targets)

    parent = {start: None}
    queue = deque([(player, start)])
    while queue:
        player_pos, crates_now = queue.popleft()
        for stand in reachable_cells(grid, crates_now, player_pos):
            for mx, my, ch in MOVES:
                crate = (stand[0] + mx, stand[1] + my)
                dest = (stand[0] + 2 * mx, stand[1] + 2 * my)
                if crate not in crates_now:
                    continue
                if (grid[dest[0]][dest[1]] == '#' or dest in crates_now
                        or dest not in alive):
                    continue
                new_crates = (crates_now - {crate}) | {dest}
                if new_crates in parent:
                    continue
                parent[new_crates] = (crates_now, player_pos, stand, (mx, my, ch))
                if new_crates == target_set:
                    chain = []
                    config = new_crates
                    while parent[config] is not None:
                        chain.append(parent[config])
                        config = parent[config][0]
                    chain.reverse()
                    moves = ''
                    for prev_config, pos, stand, (_, _, ch) in chain:
                        moves += walk_path(grid, prev_config, pos, stand)
                        moves += ch
                    return chain, moves
                # after the push the player stands on the crate's old cell
                queue.append((crate, new_crates))
    return None


# single-width unicode glyphs for board rendering
GLYPHS = {
    'wall': '▒',
    'floor': ' ',
    'target': '□',            # hollow square: the goal to fill
    'player': '☺',
    'player_on_target': '☻',  # filled counterpart of ☺, narrow width (⊙ renders wide)
    'crate': '■',
    'crate_on_target': '▣',   # crate filling the target outline
}
ARROWS = {'U': '↑', 'D': '↓', 'L': '←', 'R': '→'}


def render(grid, crates, player_pos, target_set):
    lines = []
    # skip the 1-cell safety border added in load_level
    for i in range(1, len(grid) - 1):
        row = grid[i]
        line = ''
        for j in range(1, len(row) - 1):
            cell = row[j]
            pos = (i, j)
            if pos == player_pos:
                line += GLYPHS['player_on_target'] if pos in target_set else GLYPHS['player']
            elif pos in crates:
                line += GLYPHS['crate_on_target'] if pos in target_set else GLYPHS['crate']
            elif cell == '#':
                line += GLYPHS['wall']
            elif pos in target_set:
                line += GLYPHS['target']
            else:
                line += GLYPHS['floor']
        lines.append(line)
    return '\n'.join(lines)


def main():
    grid, player, crates, targets = load_level(sys.argv[1])
    result = solve(grid, player, crates, targets)
    if result is None:
        print("No solution")
        return
    chain, moves = result
    target_set = frozenset(targets)
    print(f"Solved in {len(chain)} pushes, {len(moves)} moves")
    for i in range(0, len(moves), 80):
        print(moves[i:i + 80])
    config = frozenset(crates)
    player_pos = player
    print("--- start ---")
    print(render(grid, config, player_pos, target_set))
    for k, (_, _, stand, (mx, my, ch)) in enumerate(chain, 1):
        crate = (stand[0] + mx, stand[1] + my)
        config = (config - {crate}) | {(stand[0] + 2 * mx, stand[1] + 2 * my)}
        player_pos = crate
        print(f"--- push {k}: {ARROWS[ch]} ---")
        print(render(grid, config, player_pos, target_set))


if __name__ == '__main__':
    main()
