import sys

def main():
    data = sys.stdin.read().split()
    t = int(data[0])
    out = []
    for i in range(t):
        a, b = int(data[1 + 2 * i]), int(data[2 + 2 * i])
        out.append(f"{a + b} {a * b}")
    print("\n".join(out))

main()
