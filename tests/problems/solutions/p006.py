import sys

def main():
    data = sys.stdin.read().split()
    q = int(data[0])
    ns = [int(x) for x in data[1:1 + q]]
    m = max(ns)
    d = [0] * (m + 1)
    s = [0] * (m + 1)
    for i in range(1, m + 1):
        for j in range(i, m + 1, i):
            d[j] += 1
            s[j] += i
    print("\n".join(f"{d[n]} {s[n]}" for n in ns))

main()
