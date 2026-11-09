# Aequate

A self-hosted blackboard where students turn handwriting into checked, assisted math. v1 is for one student working alone; v2 adds private tutors teaching live to 1–5 students.

## Language

### Board and transcription

**Board**:
A canvas of free ink, owned by a student. In a session (v2) there is also one shared board.
_Avoid_: Canvas, whiteboard, page (a page is part of a board)

**Selection**:
An area of ink on a board that the student marks to be transcribed. Recognition happens only on a selection, never on unselected ink.
_Avoid_: Region, lasso, crop

**Transcription**:
The math read from a selection, which the student confirms or corrects before it counts.
_Avoid_: Recognition result, OCR output, reading

**Step**:
One confirmed line of math in a worked solution.
_Avoid_: Line (that word means ink), equation, entry

**Worked solution**:
The ordered list of steps on one board. Confirmed transcriptions are appended to its end. Steps can be edited or deleted but not reordered.
_Avoid_: Transcript, history, log

**Goal**:
What a worked solution is trying to reach, such as solve for x, simplify, factor, or evaluate. It is inferred from the first step and can be changed by the student (or the tutor, in v2).
_Avoid_: Task, problem type, objective

### Assistance

**CAS**:
Computer algebra system. The deterministic component that does all the mathematics: it checks steps, solves, and supplies the facts in every hint. It is the only judge of correctness. An LLM may reword what it says but never replaces it.
_Avoid_: Math engine, solver, checker, AI

**Check**:
The CAS verdict on whether a step follows from the step before it.
_Avoid_: Resolve, validate, grade

**Solve**:
The CAS computing the final answer from the latest step.
_Avoid_: Resolve, autoresolve, auto-solve

**Hint**:
A nudge toward the next step, drawn from a hint ladder. It never contains a verdict.
_Avoid_: Tip, suggestion, help

**Hint ladder**:
The ordered rungs of hints toward the step after the latest one, from vaguest to most explicit. The last rung is the next step itself.

**Rung**:
One level of a hint ladder: a single hint at a fixed level of detail. The four rungs are goal status, method, operation and next step.
_Avoid_: Level, tier, hint level

**Assist permissions**:
The three toggles check visible, hints allowed, and solve allowed. In v1 the student sets them through an assist level; in v2 a tutor sets them per student per session.
_Avoid_: Locks, gates, unblocks

**Assist level**:
A named preset of assist permissions that the student chooses, and can change at any time.
_Avoid_: Mode, difficulty, help level

**Ask**:
(v2) A student's request for a hint or solve that their assist permissions block. It goes to the tutor, who can approve it once.
_Avoid_: Request, I'm stuck, escalation

### People and sessions

**Admin**:
The person who installs an instance and manages its accounts.
_Avoid_: Owner, operator, superuser

**Session**:
(v2) A live lesson a tutor runs with 1–5 students on a shared board and their own boards.
_Avoid_: Lesson, class, room

**Tutor-less session**:
(v2) A session a tutor owns but does not attend, where every assist permission is on.
_Avoid_: Solo mode, self-study mode, offline mode
