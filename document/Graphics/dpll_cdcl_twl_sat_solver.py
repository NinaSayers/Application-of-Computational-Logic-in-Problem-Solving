from collections import defaultdict, deque

class SATSolver:
    def __init__(self, formula):
        """
        Initializes the SAT solver.

        Parameters:
          formula: A list of clauses, where each clause is represented as a list of integers.
                   A positive integer i represents the variable x_i, and a negative integer -i represents -x_i.
        """
        # Copy the formula so that learned clauses can be appended.
        self.clauses = [list(c) for c in formula]
        self.assignments = {}    # Maps variable -> True/False assignment.
        self.levels = {}         # Maps variable -> decision level at which it was assigned.
        self.reasons = {}        # Maps variable -> clause that forced the assignment (None for decision vars).
        self.decision_level = 0  # Current decision level.
        self.decision_stack = [] # Stack of (variable, value, level).

        # Two-Watched Literals: map literal -> list of clause indices watching it
        self.watches = defaultdict(list)
        self._init_watches()

    def _init_watches(self):
        """Initialize two watched literals per clause."""
        for ci, clause in enumerate(self.clauses):
            # If clause has only one literal, watch it twice.
            w0 = clause[0]
            w1 = clause[1] if len(clause) > 1 else clause[0]
            self.watches[w0].append(ci)
            self.watches[w1].append(ci)

    def literal_value(self, literal):
        """
        Evaluate a literal under current partial assignment.
        Returns True, False, or None if unassigned.
        """
        var = abs(literal)
        if var not in self.assignments:
            return None
        return self.assignments[var] if literal > 0 else not self.assignments[var]

    def check_clause(self, clause):
        """
        Determine clause status: 'satisfied', 'conflict', 'unit', or 'undefined'.
        If 'unit', also return the unit literal.
        """
        unassigned = 0
        last = None
        for lit in clause:
            val = self.literal_value(lit)
            if val is True:
                return ('satisfied', None)
            if val is None:
                unassigned += 1
                last = lit
        if unassigned == 0:
            return ('conflict', None)
        if unassigned == 1:
            return ('unit', last)
        return ('undefined', None)

    def _enqueue(self, var, value, level, reason):
        """
        Assign var=value at given level with reason and push onto decision stack.
        Returns the corresponding literal for propagation.
        """
        self.assignments[var] = value
        self.levels[var] = level
        self.reasons[var] = reason
        self.decision_stack.append((var, value, level))
        return var if value else -var

    def unit_propagate(self):
        """
        Perform unit propagation using two-watched literals.
        Returns a conflicting clause if conflict, else None.
        """
        queue = deque()
        # Enqueue all literals assigned at current level
        for var, val, lvl in self.decision_stack:
            if lvl == self.decision_level:
                queue.append(var if val else -var)

        while queue:
            lit = queue.popleft()
            lit_false = -lit
            # We iterate over a snapshot since watch list may change
            watchers = list(self.watches[lit_false])
            for ci in watchers:
                clause = self.clauses[ci]
                # Try to find a new literal to watch instead of lit_false
                found_replacement = False
                for l in clause:
                    if l == lit_false:
                        continue
                    if self.literal_value(l) is not False:
                        # relocate watch from lit_false to l
                        self.watches[l].append(ci)
                        self.watches[lit_false].remove(ci)
                        found_replacement = True
                        break
                if found_replacement:
                    continue

                # No replacement found: clause must be unit or conflict
                status, unit_lit = self.check_clause(clause)
                if status == 'conflict':
                    return clause
                elif status == 'unit':
                    v = abs(unit_lit)
                    if v not in self.assignments:
                        new_lit = self._enqueue(v, unit_lit > 0, self.decision_level, clause)
                        queue.append(new_lit)
        return None

    def pick_branching_variable(self):
        """
        Select next unassigned variable (naive).
        """
        all_vars = {abs(l) for c in self.clauses for l in c}
        for v in all_vars:
            if v not in self.assignments:
                return v
        return None

    def resolve(self, c1, c2, pivot):
        """
        Resolve two clauses on pivot literal.
        Returns the resolvent.
        """
        res = [l for l in c1 if l != pivot]
        for l in c2:
            if l != -pivot and l not in res:
                res.append(l)
        return res

    def conflict_analysis(self, conflict_clause):
        """
        First-UIP conflict analysis.
        Returns (learned_clause, backjump_level).
        """
        learned = conflict_clause.copy()
        cur_lvl = self.decision_level
        while True:
            # Count lits at current level
            lvl_lits = [l for l in learned if self.levels.get(abs(l), -1) == cur_lvl]
            if len(lvl_lits) <= 1:
                break
            # Find most recent one
            last = None
            for v,_,lvl in reversed(self.decision_stack):
                if lvl != cur_lvl:
                    continue
                for l in lvl_lits:
                    if abs(l) == v:
                        last = l
                        break
                if last:
                    break
            reason = self.reasons.get(abs(last))
            if not reason:
                break
            learned = self.resolve(learned, reason, last)

        # Compute backjump level
        back_lvl = 0
        for l in learned:
            lvl = self.levels.get(abs(l), 0)
            if lvl != cur_lvl and lvl > back_lvl:
                back_lvl = lvl
        return learned, back_lvl

    def backjump(self, level):
        """
        Undo assignments above given level.
        """
        new_stack = []
        for v, val, lvl in self.decision_stack:
            if lvl > level:
                self.assignments.pop(v, None)
                self.levels.pop(v, None)
                self.reasons.pop(v, None)
            else:
                new_stack.append((v, val, lvl))
        self.decision_stack = new_stack

    def solve(self):
        """
        Main CDCL loop.
        Returns a satisfying assignment or None if UNSAT.
        """
        while True:
            conflict = self.unit_propagate()
            if conflict:
                if self.decision_level == 0:
                    return None
                learned, bj = self.conflict_analysis(conflict)
                # add learned clause and set up its watches
                self.clauses.append(learned)
                ci = len(self.clauses) - 1
                w0 = learned[0]
                w1 = learned[1] if len(learned) > 1 else learned[0]
                self.watches[w0].append(ci)
                self.watches[w1].append(ci)
                # backjump and continue
                self.backjump(bj)
                self.decision_level = bj
            else:
                var = self.pick_branching_variable()
                if var is None:
                    return self.assignments
                # make a new decision
                self.decision_level += 1
                lit = self._enqueue(var, True, self.decision_level, None)
