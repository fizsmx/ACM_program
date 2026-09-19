import sys

def main():
    data = sys.stdin.read().split()
    n, limit = int(data[0]), int(data[1])
    w = sorted(int(x) for x in data[2:2 + n])
    i, j, boats = 0, n - 1, 0
    while i <= j:
        if i < j and w[i] + w[j] <= limit:
            i += 1
        j -= 1
        boats += 1
    print(boats)

main()
