import sys
from collections import Counter

def main():
    data = sys.stdin.read().split()
    t = int(data[0])
    out = []
    for i in range(1, t + 1):
        odd = sum(1 for v in Counter(data[i]).values() if v % 2)
        out.append("YES" if odd <= 1 else "NO")
    print("\n".join(out))

main()
