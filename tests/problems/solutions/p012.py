import sys

def main():
    data = sys.stdin.read().split()
    n, q = int(data[0]), int(data[1])
    pre = [0]
    for i in range(n):
        pre.append(pre[-1] + int(data[2 + i]))
    out = []
    p = 2 + n
    for _ in range(q):
        l, r = int(data[p]), int(data[p + 1]); p += 2
        out.append(str(pre[r] - pre[l - 1]))
    print("\n".join(out))

main()
