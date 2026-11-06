# Aequate

A self-hosted shared blackboard where private tutors teach math and sciences live to 1–5 students, and where students turn handwriting into checked, assisted math.

## Language

### Board and transcription

**Board**:
A canvas of free ink. A session has one shared board and one private board per student.
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
What a worked solution is trying to reach, such as solve for x, simplify, factor, or evaluate. It is inferred from the first step and can be changed by the student or tutor.
_Avoid_: Task, problem type, objective

### Assistance

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
The ordered rungs of hints for a step, from vaguest to most explicit. The last rung is the next step itself.

**Assist permissions**:
The per-student, per-session toggles a tutor sets for check visible, hints allowed, and solve allowed.
_Avoid_: Locks, gates, unblocks

**Ask**:
A student's request for a hint or solve that their assist permissions block. It goes to the tutor, who can approve it once.
_Avoid_: Request, I'm stuck, escalation

### Sessions

**Tutor-less session**:
A session a tutor owns but does not attend, where every assist permission is on.
_Avoid_: Solo mode, self-study mode, offline mode
