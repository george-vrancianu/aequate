# Student work is private to the student; access and third-party processing are per-student grants

A student's boards, steps, goals and hint usage are visible only to that student and to holders of a grant: permission, recorded with a start and an end, for someone else to see that student's work. v1 has no grants. In v2, tutor sessions and the review of tutor-less sessions create them, and purging a student ends them. The admin's UI shows only metadata (username, created and last-active dates, board count, storage used), never content, and the privacy notice says honestly that whoever runs the server can read the database. Sending a student's data to a third party (Mathpix for ink, a hosted LLM for steps) and contributing their selections as usage samples are each a setting per student, off by default. The admin turns a setting on after confirming they have consent, parental consent for minors, and Aequate records who confirmed and when. The student can always see these settings and turn them off. We chose this because students are often minors, the admin may be a parent, a school or a stranger running open sign-up, and Aequate cannot verify ages or consent. Defaults that send nothing anywhere and show nothing to anyone, plus a recorded confirmation, are the most Aequate can guarantee. Both third-party features already have a fallback (the browser recognizer, template hints), so per-student consent costs nothing in function.

## Considered Options

- **The admin sees everything.** Convenient for a parent or a school, but it makes every admin a reader of every student's work and leaves v2 tutors nothing to fit into. Rejected; a parent who should see the work can be given a grant once grants exist.
- **Consent per instance (the admin confirms once when enabling Mathpix or a hosted LLM).** Simpler, but one confirmation would cover students who signed up on their own and whom the admin never asked. Rejected.
- **An age gate at sign-up.** Self-declared ages prove nothing and invite lying. Rejected; self-registered students start with every setting off.
- **Automatic sample upload to the project.** Contradicts "no telemetry unless opted in". Samples leave the instance only as a file the admin exports and hands over.

## Consequences

- Every read of student work checks ownership or an active grant. v2 adds grants without changing that check.
- Each student has two settings, third-party processing and contribute samples, with their confirmation records. Turning on Mathpix or a hosted LLM for the instance changes nothing for a student whose setting is off.
- The sample export holds strokes, the confirmed LaTeX and the locale, shuffled, with no account id, no username and only the date. Turning the setting off excludes future exports but cannot recall a file already given.
- The privacy notice is generated from the instance's live configuration (what is stored, who can see it, cache expiry, active third parties, the student's settings, export and deletion). The admin can add text but not remove the generated parts.
- Retention: nothing expires by default; the admin may turn on a purge of accounts inactive for N months, with a preview. Boards deleted by the student sit in a trash for 30 days. Deleting an account, by the student or the admin, purges it at once. Caches hold no account ids and expire 90 days after last use. Logs keep usernames and IPs for 14 days. Purges do not reach the admin's backups.
- Students can download their data (board PDFs plus JSON of strokes, steps, goals and hint usage), including from the account-deletion screen.
