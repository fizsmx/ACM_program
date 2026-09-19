import sys

def main():
    s = sys.stdin.read().split()[0]
    x = y = 0
    seen = {(0, 0)}
    for ch in s:
        if ch == 'U':
            y += 1
        elif ch == 'D':
            y -= 1
        elif ch == 'R':
            x += 1
        else:
            x -= 1
        seen.add((x, y))
    print(x, y, len(seen))

main()
