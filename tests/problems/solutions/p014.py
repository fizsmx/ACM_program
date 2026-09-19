import sys
from collections import deque

def main():
    data = sys.stdin.read().split()
    r, c = int(data[0]), int(data[1])
    g = data[2:2 + r]
    dist = [[-1] * c for _ in range(r)]
    dq = deque()
    trees = 0
    for i in range(r):
        for j in range(c):
            if g[i][j] == 'F':
                dist[i][j] = 0
                dq.append((i, j))
            elif g[i][j] == '.':
                trees += 1
    best = 0
    burnt = 0
    while dq:
        i, j = dq.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, j + dj
            if 0 <= ni < r and 0 <= nj < c and g[ni][nj] == '.' and dist[ni][nj] == -1:
                dist[ni][nj] = dist[i][j] + 1
                best = max(best, dist[ni][nj])
                burnt += 1
                dq.append((ni, nj))
    print(best if burnt == trees else -1)

main()
