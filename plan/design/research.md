# Research

## Ideas for interface

Once you start a research task, it shows you this screen:

```
research
────────
Come up with ideas for college eating list

15m session, 1s elapsed
```

And creates and opens a text file in your preferred editor. I'll probably just have this be a config setting that runs a program with a string like `"code -n {FILE_PATH}"` (for vs code) or `"xterm -e vim {file}"` (for vim). I'll make markdown the default filetype. Then when you finish the research session, the contents of the file will be read by the client and uploaded to the server. 

If you pause the session, it will prompt you for another deadline and time amount.

```
:pause

due: 7d
chunk: 30m
```

You can also add this information in the command:

```
:pause 30 7d

or

:pause c:30 d:7d

(however I end up doing it)
```

If you close the session, it will ask you if you would like to follow up.

```
follow up? y
```

Then you'll be able to create new sessions:

```
research hackathons in Utah
time: 15m
due: 7d

research software internships in Utah
time: 15m
due: 14d

research BYU study abroad program
time: 10m
due: 21d
```

Enter goes down to the next field or creates a new session, backspace deletes a session if it's empty, ctrl + enter validates the information (highlighting empty or incorrectly filled fields, if any) and submits it.

Now the million dollar question: How do we access a research chain? Does there need to be an object (even if it's only used internally) that contains a research graph? Does it need to be a graph? Is this too complicated to actually make sense in any but a rare few scenarios?

## How is it different from a project?

My initial thinking is that a project is a collection of steps toward a tangible goal, and research just produces knowledge as output. Actually, maybe they're not that different. My current definition of a project could accurately be interpreted as an end split into the atomic actions that are its mean. So why not just start with a task and split into smaller tasks if needed? 

__My definition of "task" will assume that it is atomic, which means that it can't be usefully broken down any further.__ This kind of task should be immediately actionable given its dependencies are met (dependencies is vague, need to clarify this). I wonder if it wouldn't be a good idea to assume that every task can be further broken down unless it is marked as atomic. But this seems tedious, and I don't want to deal with remembering to mark every atomic task I create. Maybe I could have an input flag that would make it easier?

Does this work for research? It seems like it would be a common use-case to start with one research initiative and then do more based on the results of the first one, but this isn't breaking the first task down into smaller tasks. It's like a research "chain." A chain with multiple chunks of time spread over weeks or months. I need to explore how this could work. I'll pick one of the examples in the following paragraphs.

Let's list a few examples from my own list of what might be considered research and see if I can define a model that fits well with all of them

#### Come up with lunch ideas for college eating list

This could be considered part of a project ("Plan diet for college"), which could be considered part of a larger project ("get ready for college"). Is that okay, though? To have nested projects on the way to a goal? It makes sense, because that's how we break things down.

Although it's kind of a longer-term project with consistent focus requirements. But that seems like a good way to plan this kind of thing...

```
prepare for college
due sep 1, 2019

    get a good ACT score
    due july 27, 2019

        get a 30 on a practice test
            - 30h per week focus
```
> It seems like there needs to be a way to figure out how to portion this or something. What happens if I unknowingly schedule more focus time than I can actually 
```
    get enough money

        get a job (project)
        due may 31, 2017

            find local job openings and compare
            interview for at least two different jobs
    be prepared to live alone
        create a spreadsheet and make a conservative estimate about how much money I'll have, given my current job (atomic)
        make a budget based on my estimate
        get a place to live (project)
        due april 15, 2019
            - find which place I'm going to live
                - make a list of places in the price range set in my budget
                - call and apply for each of them (project--add each place that I'll apply for to this list)
                    - apartment a
                    - basement b
                    - condo c
            - sign a contract for the place where I want to live
        

(Does this need its own focus allotment? How do I work this out? College prep?)
```

What if a project could be like a plan with goals and focuses? Unless I can get a really conc, as long as it's between rete implementation plan for this, it needs to be a "later" feature., as long as it's between 
, as long as it's between 
#### 15-min: Explore options for making sure I'm doing enough things to be a good (and intere, as long as it's between sting) candidate for grad school
, as long as it's between 
This is a good example of a research idea that could easily be drawn out over a long time and, as long as it's between  produce interesting opportunities for me.

_Let's imagine a hypothetical chain of events and how their results feed into each other:_

In the first 15 min session, I identify several ideas that I would like to explore further:
* Hackathons
* Internships
* Studying abroad

So I save them in the provided markdown file.

I 'close' this research session, and it saves my file.

`:close`

Then, it asks me if I'd like to follow up, answer is yes:

`follow up? y`

Now I'm able to create requests for new research sessions:

```
research hackathons in Utah
due: 7d
time: 15m

research software internships in Utah
due: 14d
time: 15m

research BYU study abroad program
due: 21d
time: 10m
```

These will be available to integrate into my schedule. I'm not sure how, though. Where do they go? Where do any of these unplanned-for things go? If I say I want to learn about something new or solve an unanticipated problem, which slot do I put it in? I guess it doesnt' really matter, as long as I get time to focus during the day.

#### 15-min: Research eating ideas and add to eating list
#### 15-min: Make determinations about graduate school
#### 15-min: Think of ways to do something for someone else every day
#### Make list of ways to study better in Dynalist from "Study Less, Study Smart" summary on Lifehacker
#### Look at volunteer opportunities email
#### 15-min: Make list of volunteer opportunities I'm interested in and determine how to decide which ones to do