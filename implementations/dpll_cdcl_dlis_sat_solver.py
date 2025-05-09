# -*- coding: utf-8 -*-
"""
Created on Tue Apr  8 21:24:48 2025

@author: lucia
"""

import copy

class SATSolver:
    def __init__(self, formula):
        """
        Initializes the SAT solver.
        
        Parameters:
          formula: A list of clauses, where each clause is represented as a list of integers.
                   A positive integer i represents the variable x_i, and a negative integer -i represents ¬x_i.
        """
        # Copy the formula so that learned clauses can be appended.
        self.formula = formula[:]  
        self.assignments = {}    # Maps variable -> True/False assignment.
        self.levels = {}         # Maps variable -> decision level at which it was assigned.
        self.reasons = {}        # Maps variable -> clause that forced the assignment (None for decision variables).
        self.decision_level = 0  # Current decision level.
        self.decision_stack = [] # Stack storing tuples (variable, assigned value, decision level).

    def literal_value(self, literal):
        """
        Evaluates a literal given the current partial assignment.
        
        Returns:
          True if the literal is assigned True,
          False if the literal is assigned False,
          None if the variable is unassigned.
        """
        var = abs(literal)
        if var not in self.assignments:
            return None
        # For a positive literal, the assignment is the value; for a negative literal, invert the assignment.
        return self.assignments[var] if literal > 0 else not self.assignments[var]

    def check_clause(self, clause):
        """
        Determines the status of a clause with respect to current assignments.
        
        Returns a tuple (status, literal) where status is one of:
          - 'satisfied': Clause is already True under the assignment.
          - 'conflict': All literals are assigned False (the clause is unsatisfied).
          - 'unit': Exactly one literal is unassigned while all others are False (this literal must be True).
          - 'undefined': The clause is neither satisfied, conflicting, nor unit.
        """
        satisfied = False
        unassigned_count = 0
        unit_literal = None
        for literal in clause:
            val = self.literal_value(literal)
            if val is True:
                return ('satisfied', None)
            if val is None:
                unassigned_count += 1
                unit_literal = literal  # Last seen unassigned literal.
        if unassigned_count == 0:
            return ('conflict', None)
        if unassigned_count == 1:
            return ('unit', unit_literal)
        return ('undefined', None)

    def unit_propagate(self):
        """
        Repeatedly applies unit propagation.
        
        Returns:
          A conflicting clause if a conflict is found during propagation; otherwise, returns None.
        """
        changed = True
        while changed:
            changed = False
            for clause in self.formula:
                status, unit_literal = self.check_clause(clause)
                if status == 'conflict':
                    # A clause is unsatisfied → conflict!
                    return clause
                elif status == 'unit':
                    var = abs(unit_literal)
                    if var not in self.assignments:
                        # Determine the value needed to satisfy the unit clause.
                        value = (unit_literal > 0)
                        self.assignments[var] = value
                        self.levels[var] = self.decision_level
                        self.reasons[var] = clause  # Store the clause as the reason for this assignment.
                        self.decision_stack.append((var, value, self.decision_level))
                        changed = True
        return None

    def pick_branching_variable(self):
        """
        Selects the next unassigned variable using the DLIS heuristic.
        Returns (variable, value) to assign, or None if all variables are assigned.
        """
        pos_counts = {}
        neg_counts = {}
        # Count occurrences in unsatisfied clauses
        for clause in self.formula:
            status, _ = self.check_clause(clause)
            if status == 'satisfied':
                continue
            for lit in clause:
                var = abs(lit)
                if var not in self.assignments:
                    if lit > 0:
                        pos_counts[var] = pos_counts.get(var, 0) + 1
                    else:
                        neg_counts[var] = neg_counts.get(var, 0) + 1
        # Collect all variables in the formula to find unassigned ones not in any clause
        all_vars = set()
        for clause in self.formula:
            for lit in clause:
                all_vars.add(abs(lit))
        unassigned_vars = [var for var in all_vars if var not in self.assignments]
        if not unassigned_vars:
            return None
        # For variables not in pos/neg counts, set counts to 0
        for var in unassigned_vars:
            if var not in pos_counts:
                pos_counts[var] = 0
            if var not in neg_counts:
                neg_counts[var] = 0
        # Score variables based on DLIS heuristic
        scores = []
        for var in unassigned_vars:
            pos = pos_counts[var]
            neg = neg_counts[var]
            max_count = max(pos, neg)
            total = pos + neg
            scores.append((-max_count, -total, var))  # Negative for ascending sort
        scores.sort()  # Sorts by max_count (desc), then total (desc), then var (asc)
        var = scores[0][2]
        value = pos_counts[var] > neg_counts[var]
        return (var, value)

    def resolve(self, clause1, clause2, pivot):
        """
        Performs the resolution on two clauses over the pivot literal.
        
        Specifically, it returns:
          (clause1 \ {pivot}) ∪ (clause2 \ {-pivot})
        """
        new_clause = []
        for lit in clause1:
            if lit == pivot:
                continue
            if lit not in new_clause:
                new_clause.append(lit)
        for lit in clause2:
            if lit == -pivot:
                continue
            if lit not in new_clause:
                new_clause.append(lit)
        return new_clause

    def conflict_analysis(self, conflict_clause):
        """
        Conducts a simplified conflict analysis using a first-UIP style procedure.
        
        It resolves the conflict clause with the reasons of literals assigned at the current decision level
        until at most one literal from the current level remains in the learned clause.
        
        Returns:
          (learned_clause, backjump_level) where:
            learned_clause is the new clause learned from the conflict
            backjump_level is the decision level to which the solver should backtrack.
        """
        learned_clause = conflict_clause[:]  # Start with the conflicting clause.
        while True:
            count = 0
            last_literal = None
            # Count how many literals in the learned clause were assigned at the current decision level.
            for lit in learned_clause:
                if self.levels.get(abs(lit), -1) == self.decision_level:
                    count += 1
                    last_literal = lit
            if count <= 1:
                break
            # Resolve on the last literal assigned at the current level.
            reason_clause = self.reasons.get(abs(last_literal))
            if reason_clause is None:
                # If the literal is a decision literal, we cannot resolve further.
                break
            learned_clause = self.resolve(learned_clause, reason_clause, last_literal)
        # Determine the backjump level as the maximum level among all literals in the learned clause (other than the current level).
        backjump_level = 0
        for lit in learned_clause:
            lvl = self.levels.get(abs(lit), 0)
            if lvl != self.decision_level and lvl > backjump_level:
                backjump_level = lvl
        return learned_clause, backjump_level

    def backjump(self, level):
        """
        Backtracks the search to the given decision level by undoing assignments above that level.
        """
        new_stack = []
        for var, value, lvl in self.decision_stack:
            if lvl > level:
                if var in self.assignments:
                    del self.assignments[var]
                if var in self.levels:
                    del self.levels[var]
                if var in self.reasons:
                    del self.reasons[var]
            else:
                new_stack.append((var, value, lvl))
        self.decision_stack = new_stack

    def solve(self):
        """
        The main solving loop which alternates between unit propagation, conflict analysis, and branching.
        
        Returns:
          A satisfying assignment as a dictionary mapping variables to Boolean values if the formula is SAT;
          Otherwise, returns None indicating the formula is UNSAT.
        """
        while True:
            conflict = self.unit_propagate()
            if conflict:
                if self.decision_level == 0:
                    # Conflict at level 0 indicates an unsolvable (UNSAT) condition.
                    return None
                learned_clause, backjump_level = self.conflict_analysis(conflict)
                # Learn the clause by adding it to the formula.
                self.formula.append(learned_clause)
                # Backjump to the appropriate decision level.
                self.backjump(backjump_level)
                self.decision_level = backjump_level
            else:
                # Check if every variable has been assigned.
                all_vars = set()
                for clause in self.formula:
                    for literal in clause:
                        all_vars.add(abs(literal))
                if all(v in self.assignments for v in all_vars):
                    return self.assignments
                # Otherwise, choose a branching variable using DLIS.
                result = self.pick_branching_variable()
                if result is None:
                    return self.assignments
                var, value = result
                self.decision_level += 1
                self.assignments[var] = value
                self.levels[var] = self.decision_level
                self.reasons[var] = None  # Decision assignments have no reason clause.
                self.decision_stack.append((var, value, self.decision_level))