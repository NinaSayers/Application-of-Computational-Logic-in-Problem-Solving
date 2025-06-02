# Example 1: An unsatisfiable formula.
# This formula represents:
#    (x1 ∨ x2) ∧ (¬x1 ∨ x2) ∧ (¬x2)
# It forces x2 to be False (from (¬x2)) but then (x1 ∨ x2) forces x1 to be True,
# while (¬x1 ∨ x2) forces x1 to be False. There is no satisfying assignment.

formula1 = [
    [1, 2],
    [-1, 2],
    [-2]
]

# Example 2: A satisfiable formula.
# This formula represents:
#    (x1 ∨ x2) ∧ (¬x1 ∨ x2) ∧ (¬x2 ∨ x3)
# One possible solution is x1 = True, x2 = False, x3 = True.

formula2 = [
    [1, 2],
    [-1, 2],
    [-2, 3]
]

formula3 = [
    [1, -2],
    [1, -3],
    [1, -8],
    [1, -7],
    [-4, 3],
    [-5, -6],
    [-2, -3, -4],
    [-4, 6, 9],
    [-3, -7, 8],
    [1, 8],
    [1, 7],
    [4, 5, -1],
    [4, -6, -1],
    [-6, -4, -1],
    [6, -7, -1],
    [-7, 6, -1],
    [7, 6, -1]
]

formula4 = [
    [-11, 6, -12],
    [-11, 13, 16],
    [12, -16, -2],
    [-2, -4, 20, -10],
    [10, -8, 1],
    [10, 3],
    [-3, 26],
    [10, -5],
    [-1, -3, 5, 17, 18],
    [-3, -19, -18],
    [21, -6],
    [21, -17],
    [-22, -13],
    [13, 8],
    [-4, 19],
    [20, 23],
    [-20, 24],
    [25]
]