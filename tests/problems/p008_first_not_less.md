<!-- samples: 2 -->
# First Not Less

You are given a sorted array a_1 ≤ a_2 ≤ ... ≤ a_n and q queries. For each query value x, find the smallest index i such that a_i ≥ x. If no such index exists, answer -1.

## Constraints
- 1 ≤ n, q ≤ 2·10^5
- -10^9 ≤ a_i, x ≤ 10^9
- The array is sorted in non-decreasing order.

## Input
The input is given from Standard Input in the following format:

```
n q
a_1 a_2 ... a_n
x_1
x_2
...
x_q
```

## Output
Print q lines. The i-th line must contain the answer to the i-th query.

## Sample Input 1
```
5 3
1 3 3 7 9
3
8
10
```

## Sample Output 1
```
2
5
-1
```

The first query asks for the first element that is at least 3; that is a_2.

## Sample Input 2
```
1 2
5
5
6
```

## Sample Output 2
```
1
-1
```
