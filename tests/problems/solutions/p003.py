import sys

def main():
    data = sys.stdin.read().split()
    q = int(data[0])
    out = []
    for i in range(1, q + 1):
        n = int(data[i])
        z = 0
        p = 5
        while p <= n:
            z += n // p
            p *= 5
        out.append(f"{z} {sum(map(int, str(2 ** n)))}")
    print("\n".join(out))

main()
