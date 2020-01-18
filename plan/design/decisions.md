# Decisions

A decision is made through one or more decision sessions, where options are considered with breakdowns and pros and cons.

When a decision is created, it is open, which means that an option needs to be picked in order for it to be closed. As long as it is open, creating an option to make a decision session in the schedule palette.

Decisions can have deadlines.


```
(example in palette)

...

┌ decisions ─────────────────────────────────────────────┐
|                                                        |
|  Should I go to graduate school?          2d overdue   |
|                                                        |
|  Where should I live at college?          5d left      |
|                                                        |
└────────────────────────────────────────────────────────┘

...
```

```yaml
Decision:
    open: bool
#    sessions: DecisionSession[]
    options: Option[]
    deadline: String (ISO 8601 date string)

Option:
    name: string
    notes: string (Should flesh out the document idea I've been thinking about)
    pros: string[]
    cons: string[]
```
