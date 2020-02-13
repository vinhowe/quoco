# Spec system

Stores a bunch of encrypted documents in a "directory" for regular review.

Principle is that my specification for my life needs to be kept "in the air" and reviewed often so that I'm constantly considering my committments, how well they're working in the context of my life, and being honest with myself about what's not working.

That last point is especially important. One of the key features of this system needs to be that if I miss a review of spec item, that item is considered "inactive"--something that can't be used as an accurate descriptor of me as a person. This is because reviews serve two purposes:
- To allow me to reflect and constantly refine the spec such that it works for me
- To allow me to commit to the terms that I set to myself for the duration that I set until the next review.

If I don't believe that I can commit to the terms of a spec element, then I need to be able to say that it no longer accurately *describes my behavior.* This is the aim of the spec as a whole: to provide a hypothetical observer with a guide to understanding how I might act. This aim allows for a set of loose principles for writing and maintaining spec elements:
- It should be written in unambiguous, concise language
- It should account for the worst case scenarios
  - Looking at a "best case intentions, worst case situation" type thing
- It should (eventually and hypothetically) be presentable to an audience other than me

## Interface

The main issue I see is how I build a simple terminal interface that allows me to do all of the things that I want with every document. What are each of the things that I'll want to do?
- Add an element
- Remove an element
- Create a spec folder
- Move an existing element to a folder

Actually seems pretty easy. We just create a set of commands:

### 'new' to create element

`new [slug] [name]`

Where `[slug]` is either a normal name like `Time Management` or a path ending in a name like `principles/time-management`.
That's how we get documents into the directories we want--by specifying the "fully-qualified" path to it.

I don't think it's worth it for us to introduce the concept of a working directory because it becomes too much like a basic shell. And then the current directory becomes part of the state and there could be other considerations, I'm not sure. It also means that I have to make all of the commands work with relative paths, etc., in my imaginary "file system." I don't want that so I'm going to keep it really simple.

`[name]` doesn't require quotes because it is at the end and we can just substring everything beyond the slug.

### 'del' to remove element

`del [slug]`

Same syntax for `[slug]` as `new`. 

### 'group {add/remove}' to create/remove groups

`group {add/remove} [path]`

**NOT SURE WE NEED THIS ANY MORE.**

Removing a path will remove all of its children, which should prompt a confirmation 'y/n' prompt.

### 'group move' to move all children

### 'move' to move child

### 'rename' to rename child

It seems like a good strategy is just making the unique identifier for each of these elements their path. So a `dont_be_the_victim` under `/principles` would be identified as `/principles/dont_be_the_victim`.

The issue I see with this is that then paths don't get friendly names and they can have no information. Maybe that's not the best idea actuall.

Let's start from the interface and build for its requirements. It might look something like:

```
- Principles (principles)
  - Do The Best You Can With The Information You Have (principles/information-you-have)
  - Don't Be The Victim (principles/dont-be-a-victim)
```
etc.

The trick here, as I see it, is to build a map between folders and names, as defined by folders.

Just like in Unix, it should be impossible for something to be both a folder and file. This just makes things too confusing.

```
principles
  harris
    --> BOM (principles/harris/ballas) due TODAY
    --> ABBA (principles/harris/abba) due 2d ago
    --> ASDF (principles/harris/asdf) due 700d ago
  --> INDEX (principles/index) inactive
```

### `edit` to edit without reviewing

`edit [slug]`

### `review` to review

`review [slug]`

A review is an edit session where the aim is to review the plan as a whole and see if I can keep up with it. It's important to make a distinction between editing and reviewing because I want to be able to make a quick edit to a document without also being required to review the whole thing and recommit to it. Being required to review the document every time I open it up for edits would make it incredibly hard to keep up with it.
