# Check verdicts are judged over real solution sets

A check compares a step with the step before it and gives one of five verdicts: equivalent, conditional (equal except at values the step quietly excluded, which are named), one-way (the step gained solutions, as when squaring both sides), not equivalent (including a lost solution) and unknown. Only not equivalent counts as wrong. Every check is over the real numbers. Equations and inequalities are equivalent when they have the same solution set for the goal's target variable, with the other variables treated as parameters and multiplicity ignored. Proportional residuals are the fallback when no solution set can be computed. We chose this because the CAS spike showed that only solution-set comparison tells a lost root (a mistake) from a gained one (a one-way step), and only domain tracking on the unevaluated parse catches `x/x → 1`. School algebra is real-valued, and an unknown verdict must never pass for a proof. The CAS remains the only judge (see ADR 0001).

For solve goals, a chain with no wrong step can still end on a wrong answer after a one-way or conditional step. So goal reached also requires the latest step's solution set to equal the first step's. A step that drops roots counts as equivalent when none of the dropped roots solves the first step, so that removing an extraneous root is not marked as losing one.

Agreement at about 10 sampled real points (relative tolerance 1e-9), together with a clean domain check, counts as equivalent when the symbolic proof fails or times out; the provenance "numeric" is stored. `Expr.equals` is never a verdict source, because its answer depends on a random seed.

## Considered Options

- **Complex numbers by default, or switching to complex when a step contains `i`.** Rejected: switching would change old verdicts after the fact (`x² = −1 → ∅` would become wrong). v1 gives unknown, "Complex numbers aren't supported yet".
- **`√(x²) → x` as conditional.** Rejected: it is wrong on half the real line, not at isolated points, so it is not equivalent ("true only for x ≥ 0").
- **Numeric-only agreement as unknown.** Rejected: it would grey out many correct steps on hard problems, and numeric sampling never gave a false result in the spike.
- **One-way steps as not equivalent.** Rejected: squaring both sides is a legitimate method. The cost is the end-to-end comparison for solve goals.
- **Assuming variables are positive by default.** Rejected: it hides lost solutions. As a result, `A = πr² → r = √(A/π)` is not equivalent ("lost r = −√(A/π)") even though a radius is positive.

## Consequences

- A goal change re-checks every step, because the target variable changes solution sets. Editing the first step re-checks every step that dropped roots and, for solve goals, re-evaluates goal reached.
- Conditions on several variables (dividing by `y`) are flagged only as far as the spike on domain tracking for several variables delivers. Until then such steps are equivalent without a named condition.
