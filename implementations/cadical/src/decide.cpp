#include "internal.hpp"

namespace CaDiCaL {

// This function determines the next decision variable on the queue, without
// actually removing it from the decision queue, e.g., calling it multiple
// times without any assignment will return the same result.  This is of
// course used below in 'decide' but also in 'reuse_trail' to determine the
// largest decision level to backtrack to during 'restart' without changing
// the assigned variables (if 'opts.restartreusetrail' is non-zero).

int Internal::next_decision_variable_on_queue () {
  int64_t searched = 0;
  int res = queue.unassigned;
  while (val (res))
    res = link (res).prev, searched++;
  if (searched) {
    stats.searched += searched;
    update_queue_unassigned (res);
  }
  LOG ("next queue decision variable %d bumped %" PRId64 "", res,
       bumped (res));
  return res;
}

// This function determines the best decision with respect to score.
//
int Internal::next_decision_variable_with_best_score () {
  int res = 0;
  for (;;) {
    res = scores.front ();
    if (!val (res))
      break;
    (void) scores.pop_front ();
  }
  LOG ("next decision variable %d with score %g", res, score (res));
  return res;
}

int Internal::next_decision_variable () {
  if (use_scores ())
    return next_decision_variable_with_best_score ();
  else
    return next_decision_variable_on_queue ();
}

/*------------------------------------------------------------------------*/

// Implements phase saving as well using a target phase during
// stabilization unless decision phase is forced to the initial value
// of a phase is forced through the 'phase' option.

int Internal::decide_phase (int idx, bool target) {
  const int initial_phase = opts.phase ? 1 : -1;
  int phase = 0;
  if (force_saved_phase)
    phase = phases.saved[idx];
  if (!phase)
    phase = phases.forced[idx]; // swapped with opts.forcephase case!
  if (!phase && opts.forcephase)
    phase = initial_phase;
  if (!phase && target)
    phase = phases.target[idx];
  if (!phase)
    phase = phases.saved[idx];

  // The following should not be necessary and in some version we had even
  // a hard 'COVER' assertion here to check for this.   Unfortunately it
  // triggered for some users and we could not get to the root cause of
  // 'phase' still not being set here.  The logic for phase and target
  // saving is pretty complex, particularly in combination with local
  // search, and to avoid running in such an issue in the future again, we
  // now use this 'defensive' code here, even though such defensive code is
  // considered bad programming practice.
  //
  if (!phase)
    phase = initial_phase;

  return phase * idx;
}

// The likely phase of an variable used in 'collect' for optimizing
// co-location of clauses likely accessed together during search.

int Internal::likely_phase (int idx) { return decide_phase (idx, false); }

/*------------------------------------------------------------------------*/


// adds new level to control and trail
//
void Internal::new_trail_level (int lit) {
  level++;
  control.push_back (Level (lit, trail.size ()));
}

/*------------------------------------------------------------------------*/

bool Internal::satisfied () {
  if ((size_t) level < assumptions.size () + (!!constraint.size ()))
    return false;
  if (num_assigned < (size_t) max_var)
    return false;
  assert (num_assigned == (size_t) max_var);
  if (propagated < trail.size ())
    return false;
  size_t assigned = num_assigned;
  return (assigned == (size_t) max_var);
}

bool Internal::better_decision (int lit, int other) {
  int lit_idx = abs (lit);
  int other_idx = abs (other);
  if (stable)
    return stab[lit_idx] > stab[other_idx];
  else
    return btab[lit_idx] > btab[other_idx];
}

// Search for the next decision and assign it to the saved phase.  Requires
// that not all variables are assigned.

int Internal::decide () {
  assert (!satisfied ());
  START (decide);
  int res = 0;

  if ((size_t) level < assumptions.size ()) {
    const int lit = assumptions[level];
    assert (assumed (lit));
    const signed char tmp = val (lit);
    if (tmp < 0) {
      LOG ("assumption %d falsified", lit);
      res = 20;
    } else if (tmp > 0) {
      LOG ("assumption %d already satisfied", lit);
      new_trail_level (0);
      LOG ("added pseudo decision level");
      notify_decision ();
    } else {
      LOG ("deciding assumption %d", lit);
      search_assume_decision (lit);
    }

  } else if ((size_t) level == assumptions.size () && constraint.size ()) {

    int satisfied_lit = 0;  // The literal satisfying the constraint.
    int unassigned_lit = 0; // Highest score unassigned literal.
    int previous_lit = 0;

    const size_t size_constraint = constraint.size ();

#ifndef NDEBUG
    unsigned sum = 0;
    for (auto lit : constraint)
      sum += lit;
#endif

    for (size_t i = 0; i != size_constraint; i++) {
      int lit = constraint[i];
      constraint[i] = previous_lit;
      previous_lit = lit;

      const signed char tmp = val (lit);
      if (tmp < 0) {
        LOG ("constraint literal %d falsified", lit);
        continue;
      }

      if (tmp > 0) {
        LOG ("constraint literal %d satisfied", lit);
        satisfied_lit = lit;
        break;
      }

      assert (!tmp);
      LOG ("constraint literal %d unassigned", lit);

      if (!unassigned_lit || better_decision (lit, unassigned_lit))
        unassigned_lit = lit;
    }

    if (satisfied_lit) {
      constraint[0] = satisfied_lit;
      LOG ("literal %d satisfies constraint and is implied by assumptions", satisfied_lit);
      new_trail_level (0);
      LOG ("added pseudo decision level for constraint");
      notify_decision ();
    } else {
      if (size_constraint) {
        for (size_t i = 0; i + 1 != size_constraint; i++)
          constraint[i] = constraint[i + 1];
        constraint[size_constraint - 1] = previous_lit;
      }

      if (unassigned_lit) {
        LOG ("deciding %d to satisfy constraint", unassigned_lit);
        search_assume_decision (unassigned_lit);
      } else {
        LOG ("failing constraint");
        unsat_constraint = true;
        res = 20;
      }
    }

#ifndef NDEBUG
    for (auto lit : constraint)
      sum -= lit;
    assert (!sum);
#endif

  } else {

    int decision = 0;
    int idx = 0;
    int threshold = std::max(100, (int)std::sqrt(internal->max_var));

    // if (opts.dlis) {
    //   LOG ("using DLIS decision heuristic");
    //   decision = next_decision_variable_with_dlis ();
    //   // decision = pick_dlis_branch_literal ();
    //   if (!decision)
    //     LOG ("DLIS found no literal, falling back");
    // }
    
    if (opts.dlis && stats.decisions < threshold) {
      //decision = pick_dlis_branch_literal();
      idx = next_decision_variable_with_dlis ();
      LOG ("DLIS decision literal %d", decision);
    } else {
      idx = next_decision_variable ();
    }
    const bool target = (opts.target > 1 || (stable && opts.target));
    if (idx) decision = decide_phase (idx, target);
    

    if (decision) {
      stats.decisions++;
      LOG ("deciding literal %d", decision);
      search_assume_decision (decision);
    }
  }

  if (res) marked_failed = false;
  STOP (decide);
  return res;
}


} // namespace CaDiCaL
