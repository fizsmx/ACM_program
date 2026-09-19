import sys

def main():
    data = sys.stdin.read().split()
    x1, y1, x2, y2 = map(int, data[:4])
    n = int(data[4])
    enclosed = safe = 0
    for i in range(n):
        x, y = int(data[5 + 2 * i]), int(data[6 + 2 * i])
        if x1 <= x <= x2 and y1 <= y <= y2:
            enclosed += 1
            if x1 < x < x2 and y1 < y < y2:
                safe += 1
    print(enclosed, safe)

main()
