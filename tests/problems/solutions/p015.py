import sys

def main():
    data = sys.stdin.read().split()
    n, m = int(data[0]), int(data[1])
    parent = list(range(n + 1))
    size = [1] * (n + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    comps = n
    for i in range(m):
        u, v = find(int(data[2 + 2 * i])), find(int(data[3 + 2 * i]))
        if u != v:
            if size[u] < size[v]:
                u, v = v, u
            parent[v] = u
            size[u] += size[v]
            comps -= 1
    largest = max(size[i] for i in range(1, n + 1) if find(i) == i)
    print(comps, largest)

main()
