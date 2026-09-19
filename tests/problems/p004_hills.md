<!-- samples: 2 -->
# Hills in a Row

You are given an array a of n integers. A position i (2 ≤ i ≤ n-1) is called a hill if a_{i-1} < a_i and a_i > a_{i+1}. Count the hills and report the height of the tallest one.

## Input
The first line contains an integer n (1 ≤ n ≤ 2·10^5).
The second line contains n integers a_1, ..., a_n (1 ≤ a_i ≤ 10^9).

## Output
Print two integers separated by a space: the number of hills and the maximum value among all hills. If there is no hill, print "0 0".

## Examples
Input
7
1 3 2 5 4 4 1
Output
2 5

Input
3
1 2 3
Output
0 0

## Note
In the first example positions 2 and 4 are hills (values 3 and 5). Position 5 is not a hill because a_5 = a_6. In the second example the array is strictly increasing, so there is no hill.
