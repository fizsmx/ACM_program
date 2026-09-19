<!-- samples: 2 -->
# Limited Palette

A string s of lowercase letters is given together with an integer k. Find the length of the longest contiguous substring of s that contains at most k distinct letters.

## Input
The first line contains the integer k (1 ≤ k ≤ 26).
The second line contains the string s (1 ≤ |s| ≤ 2·10^5).

## Output
Print one integer, the maximum length.

## Example
Input
2
abcbbbbcccbdddadacb
Output
10

Input
1
aaabbb
Output
3

## Note
In the first example the substring "bcbbbbcccb" has only the letters b and c and length 10. Output for the second example is 3 because the longest run of a single letter has length 3.
