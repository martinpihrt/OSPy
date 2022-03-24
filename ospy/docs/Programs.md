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
