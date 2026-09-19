import sys

def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    a = list(map(int, data[1:1 + n]))
    cnt, best = 0, 0
    for i in range(1, n - 1):
        if a[i - 1] < a[i] > a[i + 1]:
            cnt += 1
            best = max(best, a[i])
    print(cnt, best)

main()
