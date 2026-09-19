<!-- samples: 1 -->
# Escape the Maze

You are given a grid with R rows and C columns. Each cell is either '.' (free) or '#' (wall). You start at the cell marked 'S' and want to reach the cell marked 'E'. In one move you can go up, down, left or right to a free cell.

Print the minimum number of moves needed, or -1 if it is impossible.

## Input
The first line contains T, the number of test cases (1 ≤ T ≤ 10).
Each test case starts with a line containing R and C (1 ≤ R, C ≤ 1000), followed by R lines of C characters each.

## Output
For each test case print one line with the answer.

## Sample Input
2
3 4
S..#
.#..
...E
2 2
S#
#E

## Sample Output
5
-1
