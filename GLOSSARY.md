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
One problem's ordered list of steps and goal changes on a board, with the board's level changes shown among them by time. A board can hold several. Confirmed transcriptions are appended to the end of the active worked solution. Steps can be edited or deleted but not reordered. Students see it labelled a problem.
_Avoid_: Transcript, history, log, problem (outside student-facing text)

**Active worked solution**:
The one worked solution on a board that newly confirmed steps join. The student picks it; ink position never decides it.
_Avoid_: Current problem, focus

**Goal**:
What a worked solution is trying to reach: solve for a variable, simplify, factor, expand or evaluate. It is either inferred from the first step or chosen by the student (or the tutor, in v2), and it may be unset.
_Avoid_: Task, problem type, objective

**Goal reached**:
The state of a worked solution whose latest step has the goal's finished form, with no wrong step between it and the first step. It is always computed and shown only when check visible is on.
_Avoid_: Done, solved, complete, finished

**Goal change**:
A record in a worked solution, between steps, that the goal changed, whether by the student, the tutor (v2) or by re-inference. It is not a step.
_Avoid_: Goal switch, retarget

### Assistance

**CAS**:
Computer algebra system. The deterministic component that does all the mathematics: it checks steps, solves, and supplies the facts in every hint. It is the only judge of correctness. An LLM may reword what it says but never replaces it.
_Avoid_: Math engine, solver, checker, AI

**Check**:
The CAS verdict on whether a step follows from the step before it.
_Avoid_: Resolve, validate, grade

**Verdict**:
The outcome of a check: equivalent, conditional (equal except where the step quietly excluded values), one-way (the step gained solutions), not equivalent, or unknown. Only not equivalent counts as wrong.
_Avoid_: Result, grade, tick, correct/incorrect

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
A named preset of assist permissions that the student chooses for one board, and can change at any time. The four levels are cumulative: each adds one permission to the level below.
_Avoid_: Mode, difficulty, help level

**Level change**:
A record on a board that the assist level changed and to which permissions. Each worked solution shows it among its steps by time. It is not a step.
_Avoid_: Mode switch, event

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
