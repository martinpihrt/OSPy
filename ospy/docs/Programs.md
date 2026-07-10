OSPy Programs
====

Internally, all programs maintain a schedule that can be modified directly (just like the custom program).
To allow for easier manipulation, the following types of programs have been created.
Each program can be of one of these types. In the end, every program can also be written as a custom program.
<br/><br/>

| Prog/type_data  |             0                |     1          |      2         |     3         |      4         |     5        |
|              --:|:--                           |:--             |:--             |:--            |:--             |:--           |
| DAYS_SIMPLE     |start_time                    |duration        |repeat pause    |repeat times   |list days to run|              |
| REPEAT_SIMPLE   |start_time                    |duration        |repeat pause    |repeat times   |repeat days     |start_date    |
| DAYS_ADVANCED   |list of intervals [start, end]|list days to run|                |               |                |              |
| REPEAT_ADVANCED |list of intervals [start, end]|repeat days     |                |               |                |              |
| WEEKLY_ADVANCED |list of intervals [start, end]|                |                |               |                |              |
| CUSTOM          |list of intervals [start, end]|                |                |               |                |              |


    set_days_simple start_min, duration_min, pause_min, repeat_times, [days] 
    set_repeat_simple start_min, duration_min, pause_min, repeat_times, repeat_days, start_date 
    set_days_advanced [schedule], [days] 
    set_repeat_advanced [schedule], repeat_days, start_date 
    set_weekly_advanced [schedule] 

Program group postponement
----

A program group postponement is a one-time scheduler overlay. It does not rewrite a program's `start`, `schedule`, type data, enabled days, or later recurring runs. The administrator selects a new date and start time for the group. OSPy obtains the nearest future eligible occurrence of every enabled program in that group from `predicted_schedule()`, uses the earliest resulting start as the group anchor, and shifts the selected occurrences by one common time delta. This preserves their scheduler-resolved order, durations, and relative gaps. An occurrence temporarily blocked by rain or by a disabled scheduler remains eligible for postponement, while an occurrence rejected by the program cut-off or a scheduler error is not copied.

The source occurrence UIDs and a minimal snapshot of the shifted station intervals are persisted in `options.program_group_postponements`. Each record contains a random postponement ID, group ID, creation time, original and target ranges, shift in seconds, and the selected station runs. Because the record is stored in `options.db`, it remains active after an OSPy service restart. Only one active postponement can exist for a group, the target must be later than the original anchor, and the target is limited to 30 days in the future.

During schedule prediction, `programs.apply_group_postponements()` removes only the recorded source UIDs and adds deterministic shifted replacement UIDs. The replacements are automatic runs (`manual=False`), so scheduler enablement, rain blocks, the rain sensor, output usage limits, master-station control, and station delays still apply. Their durations are fixed to the snapshot calculated when the postponement was created, preventing a later prediction from applying the water-level duration adjustment twice.

Before a snapshot is applied, OSPy verifies that the referenced program still exists, is enabled, remains in the same group, and still has the same stations and schedule. A stale snapshot is not allowed to run or suppress a different program after deletion, reindexing, moving, disabling, or material editing. A group with a pending postponement record cannot be deleted.

Cancelling before the original start removes the overlay and restores the normal source occurrence. Cancelling after the original start keeps a temporary cancellation tombstone until the original source range has passed; this prevents the missed source run from starting late, while the postponed replacement is no longer generated. Completed records are removed after their target range has passed, while normal run history remains in the log.

Creating and cancelling postponements is available only on the administrator Programs page. Both actions use `POST`, pass through the standard `ProtectedPage` CSRF verification, validate all group and date/time values again on the server, use a lock for concurrent updates, and write an event-log entry when event logging is enabled. The browser submits only the group ID and requested target time; the server always calculates the affected occurrences itself.
