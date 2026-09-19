<!-- samples: 3 -->
# Broken Stairs

A staircase has n steps numbered 1 to n. You start on the ground (step 0) and in one move you may climb either 1 or 2 steps. Some steps are broken and you must never stand on them. Count the number of different ways to reach step n, modulo 10^9 + 7.

## Input
The first line contains n and m (1 ≤ n ≤ 10^6, 0 ≤ m ≤ n), the number of steps and the number of broken steps.
The second line contains m distinct integers, the broken steps (each between 1 and n). The line is empty when m = 0.

## Output
Print the number of ways modulo 10^9 + 7.

Example 1:
Input:
5 1
3
Output:
2
Explanation: The valid routes are 0-1-2-4-5 and 0-2-4-5.

Example 2:
Input:
4 0

Output:
5

Example 3:
Input:
6 2
2 3
Output:
0
Explanation: Steps 2 and 3 are both broken, so step 4 can never be reached.

Constraints:
The answer must be printed modulo 1000000007.
