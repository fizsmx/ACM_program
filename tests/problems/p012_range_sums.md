<!-- samples: 1 -->
# Range Sum Queries

You are given an array of n integers and q queries. Each query gives two indices l and r (1-based, l ≤ r) and asks for the sum of the elements a_l + a_{l+1} + ... + a_r.

### Input
The first line contains n and q (1 ≤ n, q ≤ 2·10^5).
The second line contains n integers a_i (-10^9 ≤ a_i ≤ 10^9).
Each of the next q lines contains l and r (1 ≤ l ≤ r ≤ n).

### Output
For each query print the requested sum on its own line.

### Sample Input
```
5 3
1 2 3 4 5
1 3
2 5
4 4
```

### Sample Output
```
6
14
4
```
