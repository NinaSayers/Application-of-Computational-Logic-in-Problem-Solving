# restart_luby.py

def luby(u, k):
    """
    Generates the k-th value of the Luby sequence multiplied by u (unit run).
    """
    def _luby(i):
        # Encuentra el mayor j tal que i = 2^j - 1
        j = 1
        while (1 << j) - 1 < i:
            j += 1
        if i == (1 << j) - 1:
            return 1 << (j - 1)
        return _luby(i - (1 << (j - 1)) + 1)
    return u * _luby(k)

class SATSolverLuby:
    def __init__(self, formula, unit_run=100):
        self.formula = formula[:]  
        self.assignments = {}
        self.levels = {}
        self.reasons = {}
        self.decision_level = 0
        self.decision_stack = []
        # Luby restart parameters
        self.unit_run = unit_run
        self.luby_idx = 1
        self.conflicts_since_restart = 0
        self.next_restart = luby(self.unit_run, self.luby_idx)

    # the same functions (literal_value, check_clause, unit_propagate,
    # pick_branching_variable, resolve, conflict_analysis, backjump)

    def solve(self):
        while True:
            conflict = self.unit_propagate()
            if conflict:
                self.conflicts_since_restart += 1
                if self.decision_level == 0:
                    return None
                learned_clause, backjump_level = self.conflict_analysis(conflict)
                self.formula.append(learned_clause)
                self.backjump(backjump_level)
                self.decision_level = backjump_level

                # restart?
                if self.conflicts_since_restart >= self.next_restart:
                    # Restart: clear assignments, preserve learned clauses
                    self.assignments.clear()
                    self.levels.clear()
                    self.reasons.clear()
                    self.decision_stack.clear()
                    self.decision_level = 0
                    # Prepare next umbral
                    self.luby_idx += 1
                    self.next_restart = luby(self.unit_run, self.luby_idx)
                    self.conflicts_since_restart = 0
            else:
                var = self.pick_branching_variable()
                if var is None:
                    return self.assignments
                self.decision_level += 1
                self.assignments[var] = True
                self.levels[var] = self.decision_level
                self.reasons[var] = None
                self.decision_stack.append((var, True, self.decision_level))


