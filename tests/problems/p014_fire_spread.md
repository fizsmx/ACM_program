<!-- samples: 2 -->
# Forest Fire

A rectangular forest is described by a grid with R rows and C columns. Every cell is either a tree '.', a rock '#', or a burning tree 'F'. Each minute, every burning tree sets fire to all trees in the four neighbouring cells (up, down, left, right). Rocks never burn.

Determine after how many minutes every tree in the forest is burning. If some tree can never catch fire, print -1. If there are no unburnt trees at the start, print 0.

## Input
The first line contains R and C (1 ≤ R, C ≤ 1000). The next R lines each contain C characters from the set {'.', '#', 'F'}. There is at least one 'F'.

## Output
Print a single integer, the number of minutes, or -1.

## Sample Input 1
3 4
F...
.#..
...F

## Sample Output 1
2

## Sample Input 2
2 3
F#.
.#.

## Sample Output 2
-1
