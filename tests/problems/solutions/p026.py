import sys

def main():
    data = sys.stdin.read().split()
    t = int(data[0])
    ns = [int(x) for x in data[1:1 + t]]
    limit = max(ns) + 200
    sieve = bytearray([1]) * (limit + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, int(limit ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = bytearray(len(range(i * i, limit + 1, i)))
    nxt = [0] * (limit + 2)
    last = 0
    for i in range(limit, -1, -1):
        if sieve[i]:
            last = i
        nxt[i] = last
    print("\n".join(str(nxt[n]) for n in ns))

main()
