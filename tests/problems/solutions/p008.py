import sys
from bisect import bisect_left

def main():
    data = sys.stdin.read().split()
    n, q = int(data[0]), int(data[1])
    a = [int(x) for x in data[2:2 + n]]
    out = []
    for i in range(q):
        x = int(data[2 + n + i])
        p = bisect_left(a, x)
        out.append(str(p + 1) if p < n else "-1")
    print("\n".join(out))

main()
