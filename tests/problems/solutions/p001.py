import sys
from collections import Counter

def main():
    data = sys.stdin.read().split()
    n, k = int(data[0]), int(data[1])
    a = list(map(int, data[2:2 + n]))
    seen = Counter()
    total = 0
    for x in a:
        total += seen[k - x]
        seen[x] += 1
    print(total)

main()
