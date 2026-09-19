<!-- samples: 1 -->
# Bracket Check

A sequence of brackets is well-formed if every opening bracket is closed by a matching closing bracket of the same type and the pairs are properly nested. The bracket types are (), [] and {}.

Input
The first line contains T (1 ≤ T ≤ 1000), the number of sequences. Each of the next T lines contains a non-empty sequence of at most 10^5 bracket characters.

Output
For each sequence print "valid" if it is well-formed and "invalid" otherwise.

Sample Input
5
([]{})
([)]
((
{}
]

Sample Output
valid
invalid
invalid
valid
invalid
