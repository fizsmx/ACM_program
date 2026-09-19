import sys

def main():
    data = sys.stdin.read().split()
    n, q = int(data[0]), int(data[1])
    a = [int(x) for x in data[2:2 + n]]
    out = []
    for k in range(q):
        t = int(data[2 + n + k])
        i, j = 0, n - 1
        found = False
        while i < j:
            s = a[i] + a[j]
            if s == t:
                found = True
                break
            if s < t:
                i += 1
            else:
                j -= 1
        out.append("YES" if found else "NO")
    print("\n".join(out))

main()
