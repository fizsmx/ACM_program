<!-- samples: 2 -->
# Painted Segments

A long straight road is painted in n operations. The i-th operation paints every point of the segment [l_i, r_i]. Two painted segments that overlap or touch at an endpoint form one continuous painted stripe. After all operations, report how many separate stripes there are and the total painted length.

## Input
The first line contains n (1 ≤ n ≤ 2·10^5).
Each of the next n lines contains two integers l_i and r_i (0 ≤ l_i < r_i ≤ 10^9).

## Output
Print two integers: the number of stripes and the total painted length.

## Examples
Input
4
1 3
2 6
8 10
15 18
Output
3 10

Input
2
1 4
4 5
Output
1 4

## Note
In the first example the segments [1, 3] and [2, 6] merge into the stripe [1, 6] of length 5; together with [8, 10] and [15, 18] the painted length is 5 + 2 + 3 = 10. In the second example the segments touch at the point 4 and form a single stripe [1, 5].
