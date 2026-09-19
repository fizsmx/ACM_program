import sys
from collections import defaultdict

def main():
    data = sys.stdin.read().split()
    k = int(data[0])
    s = data[1]
    cnt = defaultdict(int)
    best = 0
    left = 0
    distinct = 0
    for right, ch in enumerate(s):
        if cnt[ch] == 0:
            distinct += 1
        cnt[ch] += 1
        while distinct > k:
            cnt[s[left]] -= 1
            if cnt[s[left]] == 0:
                distinct -= 1
            left += 1
        best = max(best, right - left + 1)
    print(best)

main()
