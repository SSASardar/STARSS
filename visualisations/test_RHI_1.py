import numpy as np
import matplotlib.pyplot as plt
import re

filename = "outputs/radar_scan_0039.txt"

def parse_first_scan(filename):
    n_angles = None
    n_ranges = None
    grid_size = None
    data_tokens = []

    with open(filename, "r") as f:
        inside = False
        for raw in f:
            line = raw.strip()
            if line.startswith("=== BEGIN RADAR_SCAN"):
                inside = True
                continue
            if line.startswith("=== END RADAR_SCAN"):
                break
            if not inside:
                continue

            # parse simple key=value lines
            if line.startswith("box.num_angles="):
                n_angles = int(line.split("=",1)[1])
            elif line.startswith("box.num_ranges="):
                n_ranges = int(line.split("=",1)[1])
            elif line.startswith("grid.size="):
                grid_size = int(line.split("=",1)[1])
            elif line.startswith("grid.data="):
                # everything after '=' on this line is the first data chunk
                part = line.split("=",1)[1].strip()
                if part:
                    data_tokens.extend(part.split())
                # now continue reading subsequent lines until we collected enough tokens
                while (grid_size is None or len(data_tokens) < grid_size):
                    # peek next line but ensure we don't pass END block
                    pos = f.tell()
                    nxt = f.readline()
                    if not nxt:
                        break
                    nxt_s = nxt.strip()
                    if nxt_s.startswith("=== END RADAR_SCAN"):
                        # rewind one line so outer loop sees the END marker, then break
                        f.seek(pos)
                        break
                    # append tokens (ignore '...' placeholders)
                    tokens = [t for t in nxt_s.split() if t != '...']
                    if not tokens:
                        continue
                    data_tokens.extend(tokens)

    if n_angles is None or n_ranges is None:
        raise ValueError("Missing box.num_angles or box.num_ranges in the first scan.")
    if grid_size is None:
        grid_size = n_angles * n_ranges

    # Remove any stray non-numeric tokens (safety)
    numeric_tokens = []
    float_re = re.compile(r'^[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?$')
    for t in data_tokens:
        if float_re.match(t):
            numeric_tokens.append(t)
        # else skip tokens like '...'

    if len(numeric_tokens) < n_angles * n_ranges:
        raise ValueError(f"Not enough numeric grid values: got {len(numeric_tokens)}, expected {n_angles*n_ranges}")

    arr = np.array(numeric_tokens[: n_angles * n_ranges], dtype=float)
    return arr, n_angles, n_ranges

def build_grid_from_indexing(arr, n_angles, n_ranges):
    """
    arr[k] corresponds to k = range_id + num_angles * angle_id
    So for each angle a: arr[start : start + n_ranges] maps to grid[a, :]
    where start = n_angles * a
    """
    grid = np.empty((n_angles, n_ranges), dtype=arr.dtype)
    for a in range(n_angles):
        start = n_angles * a
        grid[a, :] = arr[start : start + n_ranges]
    return grid

if __name__ == "__main__":
    arr, n_angles, n_ranges = parse_first_scan(filename)
    grid = build_grid_from_indexing(arr, n_angles, n_ranges)

    # Optional sanity check: shape and a small print
    print(f"Parsed grid: angles={n_angles}, ranges={n_ranges}, total={arr.size}")
    print("grid shape:", grid.shape)

    # Plot heatmap
    plt.figure(figsize=(10,6))
    # each row = angle, each column = range
    im = plt.imshow(grid, aspect='auto', origin='lower', cmap='viridis')
    plt.colorbar(im, label='Value')
    plt.xlabel('Range gate index')
    plt.ylabel('Angle index')
    plt.title('Radar grid heatmap (first scan) — index = range + num_angles*angle')
    plt.tight_layout()
    plt.show()

