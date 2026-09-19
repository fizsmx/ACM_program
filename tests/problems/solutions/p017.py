import sys

MOD = 10 ** 9 + 7

def main():
    data = sys.stdin.read().split()
    n, m = int(data[0]), int(data[1])
    broken = set(int(x) for x in data[2:2 + m])
    prev2, prev1 = 0, 1  # dp[-1], dp[0]
    for step in range(1, n + 1):
        cur = 0 if step in broken else (prev1 + prev2) % MOD
        prev2, prev1 = prev1, cur
    print(prev1)

main()
