import sys

def lcs(a, b):
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            cur[j] = prev[j - 1] + 1 if ca == cb else max(prev[j], cur[j - 1])
        prev = cur
    return prev[-1]

def main():
    data = sys.stdin.read().split()
    t = int(data[0])
    out = []
    for i in range(t):
        out.append(str(lcs(data[1 + 2 * i], data[2 + 2 * i])))
    print("\n".join(out))

main()
