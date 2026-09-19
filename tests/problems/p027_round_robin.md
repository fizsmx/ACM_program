<!-- samples: 2 -->
# Round Robin Scheduler

A single CPU runs n processes with a round-robin scheduler. The processes are placed in a queue in the order 1, 2, ..., n. The scheduler repeatedly takes the process at the front of the queue and runs it for at most q time units (the quantum). If the process still needs more CPU time it goes to the back of the queue; otherwise it finishes and leaves. Context switches take no time.

Report the order in which the processes finish and the finishing time of every process.

## Input
The first line contains n and q (1 ≤ n ≤ 10^5, 1 ≤ q ≤ 10^9).
The second line contains n integers t_1, ..., t_n (1 ≤ t_i ≤ 10^9), the CPU time needed by each process.

## Output
Print two lines. The first line contains the process numbers in the order they finish. The second line contains n integers, where the i-th integer is the finishing time of process i.

Example 1:
Input:
3 2
5 3 1
Output:
3 2 1
9 8 5
Explanation: Process 1 runs during [0, 2), process 2 during [2, 4), process 3 finishes at time 5, then process 1 runs during [5, 7), process 2 finishes at time 8 and finally process 1 finishes at time 9.

Example 2:
Input:
2 10
4 4
Output:
1 2
4 8

Constraints:
The sum of all t_i fits in a 64-bit signed integer.
