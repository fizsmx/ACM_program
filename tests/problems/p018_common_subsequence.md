<!-- samples: 1 -->
# Shared Melody

Two melodies are written as strings of lowercase letters. The similarity of two melodies is the length of their longest common subsequence: the longest string that can be obtained from both melodies by deleting zero or more letters without changing the order of the remaining ones. Compute the similarity for several pairs.

Input
The first line contains T (1 ≤ T ≤ 20). Each of the next T lines contains two strings a and b separated by a space (1 ≤ |a|, |b| ≤ 2000).

Output
For each pair print the similarity on its own line.

Example Input
3
abcde ace
abc def
programming gaming

Example Output
3
0
6
