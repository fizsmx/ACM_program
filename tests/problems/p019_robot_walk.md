<!-- samples: 2 -->
# Robot Walk

A robot starts at cell (0, 0) of an infinite grid and receives a string of commands. The command U increases y by 1, D decreases y by 1, R increases x by 1 and L decreases x by 1. After executing all commands report the final position and how many distinct cells the robot has stood on, counting the starting cell.

## Input
A single line with the command string (1 ≤ length ≤ 2·10^5) consisting of the letters U, D, L and R.

## Output
Print three integers: the final x, the final y and the number of distinct cells visited.

## Examples

Input:
```
UURDDL
```
Output:
```
0 0 6
```

Input:
```
RRLL
```
Output:
```
0 0 3
```
