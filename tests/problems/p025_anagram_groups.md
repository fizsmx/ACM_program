<!-- samples: 2 -->
# Anagram Families

Two words are anagrams if one can be obtained from the other by rearranging its letters. A family is a maximal set of words from the list that are all anagrams of each other. Given a list of words, find how many families there are and the size of the largest family.

## Input
The first line contains n (1 ≤ n ≤ 10^5).
The second line contains n words separated by single spaces. Every word consists of 1 to 20 lowercase letters. Words may repeat; repeated words count as separate members of their family.

## Output
Print two integers separated by a space: the number of families and the size of the largest family.

## Examples
Input
6
listen silent enlist google gogole cat
Output
3 3

Input
3
abc bca cab
Output
1 3
