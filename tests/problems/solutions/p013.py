import sys

def main():
    data = sys.stdin.read().split()
    t = int(data[0])
    pair = {')': '(', ']': '[', '}': '{'}
    opening = set(pair.values())
    out = []
    for i in range(1, t + 1):
        st = []
        ok = True
        for ch in data[i]:
            if ch in opening:
                st.append(ch)
            elif not st or st.pop() != pair[ch]:
                ok = False
                break
        out.append("valid" if ok and not st else "invalid")
    print("\n".join(out))

main()
