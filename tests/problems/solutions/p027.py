import sys
from collections import deque

def main():
    data = sys.stdin.read().split()
    n, q = int(data[0]), int(data[1])
    need = [int(x) for x in data[2:2 + n]]
    dq = deque(range(n))
    finish = [0] * n
    order = []
    now = 0
    while dq:
        p = dq.popleft()
        run = min(q, need[p])
        now += run
        need[p] -= run
        if need[p] == 0:
            finish[p] = now
            order.append(p + 1)
        else:
            dq.append(p)
    print(" ".join(map(str, order)))
    print(" ".join(map(str, finish)))

main()
