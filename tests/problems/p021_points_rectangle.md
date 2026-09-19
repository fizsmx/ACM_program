<!-- samples: 2 -->
# Fenced Garden

A rectangular garden is fenced along the axis-aligned rectangle with lower-left corner (x1, y1) and upper-right corner (x2, y2). There are n flowers at integer coordinates. A flower is enclosed if it lies inside the rectangle or on its boundary, and it is safe if it lies strictly inside (not touching the fence). Count the enclosed flowers and the safe flowers.

## Input
The first line contains four integers x1 y1 x2 y2 (-10^9 ≤ x1 < x2 ≤ 10^9, -10^9 ≤ y1 < y2 ≤ 10^9).
The second line contains n (1 ≤ n ≤ 10^5).
Each of the next n lines contains the coordinates x y of one flower (-10^9 ≤ x, y ≤ 10^9).

## Output
Print two integers separated by a space: the number of enclosed flowers and the number of safe flowers.

## Sample Input 1
0 0 4 3
5
0 0
2 2
4 3
5 1
1 3

## Sample Output 1
4 1

## Sample Input 2
-1 -1 1 1
2
0 0
2 2

## Sample Output 2
1 1
