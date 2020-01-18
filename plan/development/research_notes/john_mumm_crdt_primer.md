# Notes on A CRDT Primer: Defanging Order Theory by John Mumm

[Link](https://www.youtube.com/watch?v=OOlnp2bZVRs)

The example he's providing at the beginning is a distributed counter for a like button, where different users send their likes to different servers.

> With CRDTs, we only need gossip to converge on the truth.

1. Introduction to Order Theory
    
    1. Total and partial orders
    2. JOins
    3. Join semi-lattices
2. Convergent CRDTs
    1. CRDT interface
    2. Implement G-counter
    3. "monotonic join semi-lattice"

To understand join semi-lattices, we need three core concepts:
1. a <= b order
2. a || b incomparability
3. a v b join (get join symbol)

We can compare elements in a normal

{0,1,2,3,4,5,6,7,...}

![](images/2019-04-25-13-35-54.png)

CRDTs are interested in partial orders, which means that it means that not every a and b must be comparable. This is a || b, incomparability.

NYC < US

NYC || Seattle

![](images/2019-04-25-13-37-21.png)

We can compare the earth and india, and the earth and delhi, and that means that they are comparable

![](images/2019-04-25-13-37-58.png)

So the US and India are incomparable because they're not within the same tree

Now he's talking about "vector clock timestamps." I think this means that there are multiple timestamps, because a scalar timestamp would only have one.

Yeah, because he represents it like a series of integers (1, 4, 2)

So if we take two vector clocks, v1 and v2, v1 <= v2 only if every element in v2 is greater than or equal to every element in v1.

![](images/2019-04-25-13-42-49.png)

So if there isn't a consistent inequality in all the elements of the vector, then v1 || v2, and they happened "concurrently."

![](images/2019-04-25-13-44-14.png)

Not sure what's going on here:

![](images/2019-04-25-13-46-51.png)

He says it's an ordered set.

If we take a subset of an ordered set, then an "upper bound" of that set will be greater than or equal to every element in the set.

![](images/2019-04-25-13-48-49.png)

5 is an upper bound because it's greater than, 4 because it's equal to.

Now we're going to say that we have a subset P of S, with two elements. (Apparently they don't necessarily have to be adjacent)

The join of any two elements is the "least upper bound," so the lowest (available?) value that is greater than both of them. What happens when there is no least upper bound available in the set?

So when two elements are compared directly, the join is the max of the two of them.

He goes back to the diagram of vector clocks we saw earlier.

![](images/2019-04-25-13-54-26.png)

In trying to compare (1, 0, 0), and (0, 1, 1), we find that they are incomparable (||), according to our earlier definition. We have to find the lowest element that is greater than or equal to both vectors.

![](images/2019-04-25-13-55-49.png)

(1,1,1) is this element.

![](images/2019-04-25-14-01-07.png)

for Bronx v Queens, which are incomparable, the upper bound is NYC. The other diagram made more sense. If we did 3 v 3, the upper bound would be 3. No, okay, so they're on the same level, but they're not the same thing. This makes more sense. He goes on to explain that NYC v NYC = NYC.

![](images/2019-04-25-14-05-57.png)

Haha he messed up the slide. Joins move up.

![](images/2019-04-25-14-06-46.png)

So there is no join here because there isn't a greatest element. It looks like nothing could be joined here at all.

There are three laws that CRDT follows, according to John.

#### Associativity:

(a v b) v c = a v (b v c)

The order of joins doesn't matter.

#### Commutativity

a v b = b v a

(This seems like the same thing as associativity. Order doesn't matter.)

#### Idempotence

a v a = a

Seems simple enough. a is always >= a.

### Definition of a join semi-lattice

If any two pairs in ordered set S have a valid join, then it is a join semi-lattice.

I was just thinking it would be nice if there was a formula that represented this.

> If x v y exists for all {x,y} in S, then S is a join semi-lattice.

This is cool. He moves on to "convergent CRDTs"

### Convergent CRDTs

He's talking about "state-based CRDTs," but there's another kind apparently.

> As we merge these CRDTs across nodes, they converge toward a global value.

Going back to BirdWatch...

![](images/2019-04-25-14-18-21.png)

So the servers receive local state updates and pass them to each-other, "at their own leisure." He calls this "gossip." CRDT is supposedly able to handle this. This is really phlicking interesting. Could I do a mostly distributed system for perora?

> For state-based CRDTs, we need three things.

> 1. A state type S ordered by some <S, <=>> (S should be ordered, I assume that "<S, <=>" is notation for that)

> 2. A merge() function that merges two states

(This sounds like it would require a central server)

> 3. An update() function that updates a local state with downstream information

He says that "everything should converge toward a global value."

Associativity and Commutativity means that the order of things doesn't matter.

Idempotence means that the same state can be merged in multiple times(Meaning that you can send the same state in multiple times without ill effect).

> The Global Value doesn't necessarily exist on any one node

like cy"
like 
like nt it
like 
A "G-counter" is a grow-only counter. I looked it up and some article says that this is the simplest CRDT example.

Going back to the three requirements of state-based CRDTs. He added a value() function that will return the value to the end-user.

So he presents a naive approach that just outlines a naive approach.

* value() returns the local state, which is just an integer
* update() adds one to the local state
* merge(x) = x + local state

Now I'm guessing he's going to tell us why this doesn't work, because he already said that with CRDTs, you can pass the same thing in multiple times. You couldn't do that with this system, as far as I can see.

Yeah, that's exactly what he did. It's not idempotent.

He proposes that we replace merge with merge(x) = max(x, local state). This also sounds like a bad idea.

So he says that the local state should be a vector instead.

So I'll try to put what he's doing in my own words. Each node stores their own version of a vector that represents the number of increments in each of the nodes. Whenever a node gets a new vector, it takes the max of the two vectors and uses that as its local state.

What is this "gossip protocol"? How do servers decide how frequently to share their versions of state?

### THE MONOTONIC JOIN SEMI-LATTICE

This means that CRDTs are always moving toward a global value, even if they might never reach it. (This strikes me as very similar to the idea of limits in calculus. We're always approaching some value.)

## Resources:

* https://github.com/jtfmumm/curryon2018