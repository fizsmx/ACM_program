import sys
from collections import Counter

def main():
    s = sys.stdin.read().split()[0]
    c = Counter(s)
    best = max(c.items(), key=lambda kv: (kv[1], kv[0]))
    print(best[0], best[1])

main()
