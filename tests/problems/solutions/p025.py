import sys
from collections import Counter

def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    fam = Counter("".join(sorted(w)) for w in data[1:1 + n])
    print(len(fam), max(fam.values()))

main()
