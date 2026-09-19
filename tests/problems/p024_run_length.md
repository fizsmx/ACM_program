<!-- samples: 3 -->
# Compress the Word

A word made of lowercase letters is compressed as follows: every maximal block of equal consecutive letters is replaced by the letter followed by the length of the block. For example, the block "aaa" becomes "a3". Print the compressed form of the given word.

## Constraints
- 1 ≤ |S| ≤ 2·10^5
- S consists of lowercase English letters.

## Input
The input is given from Standard Input in the following format:

S

## Output
Print the compressed word.

## Sample Input 1
aaabccdddd

## Sample Output 1
a3b1c2d4

## Sample Input 2
z

## Sample Output 2
z1

Even a block of a single letter gets its length written after it.

## Sample Input 3
abab

## Sample Output 3
a1b1a1b1
