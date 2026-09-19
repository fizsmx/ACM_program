import sys
from collections import deque

def main():
    data = sys.stdin.read().split()
    pos = 0
    t = int(data[pos]); pos += 1
    out = []
    for _ in range(t):
        r, c = int(data[pos]), int(data[pos + 1]); pos += 2
        g = data[pos:pos + r]; pos += r
        start = end = None
        for i in range(r):
            for j in range(c):
                if g[i][j] == 'S':
                    start = (i, j)
                elif g[i][j] == 'E':
                    end = (i, j)
        dist = [[-1] * c for _ in range(r)]
        dq = deque([start])
        dist[start[0]][start[1]] = 0
        while dq:
            i, j = dq.popleft()
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < r and 0 <= nj < c and g[ni][nj] != '#' and dist[ni][nj] == -1:
                    dist[ni][nj] = dist[i][j] + 1
                    dq.append((ni, nj))
        out.append(str(dist[end[0]][end[1]]))
    print("\n".join(out))

main()
