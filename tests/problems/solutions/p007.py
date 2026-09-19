import sys

def main():
    lines = sys.stdin.read().split("\n")
    n = int(lines[0])
    rows = []
    for i in range(1, n + 1):
        name, sc = lines[i].split()
        rows.append((-int(sc), name))
    rows.sort()
    print("\n".join(name for _, name in rows))

main()
