import sys

def main():
    data = sys.stdin.read().split()
    t = int(data[0])
    out = []
    for i in range(1, t + 1):
        s = data[i]
        n = int(s)
        root = 1 + (n - 1) % 9
        out.append(f"{root} {int(s[::-1])}")
    print("\n".join(out))

main()
