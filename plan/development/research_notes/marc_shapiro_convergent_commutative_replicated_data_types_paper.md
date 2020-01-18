# Notes from [A comprehensive study of Convergent and Commutative Replicated Data Types](https://hal.inria.fr/inria-00555588/document)

#### Definition of _a priori:_

> 1. relating to or denoting reasoning or knowledge which proceeds from theoretical deduction rather than from observation or experience.

From the sentence:

> A replica may execute an operation without synchronising a priori with other replicas.

They talk about something called _Treedoc_, which is defined in [this paper](https://www.google.com/search?client=ubuntu&channel=fs&q=treedoc&ie=utf-8&oe=utf-8). May be worth checking out, along with the [RGASplit](https://pages.lip6.fr/Marc.Shapiro/papers/rgasplit-group2016-11.pdf) (Mark Shapiro's name keeps popping up here).

> In the future, we plan to extend the approach to data types where common-case, time-critical operations are commutative and rare operations require synchronisation but can be delayed to periods when the network is well connected.

If I understand this quote right, I think exploring this would be interesting to me.

They used the word "linearizability," which is a math adjective that describes the ease with which something can be made linear. I'm not sure how this applies here, but I'm going to keep looking for this term.

From [this paper](https://run.unl.pt/bitstream/10362/7802/1/Sousa_2012.pdf):

> The concurrent execution of operations in a replicated shared object is said to be linearizable if operation appear to have executed atomically, in some sequential order that is consistent with the real time at which the operations occurred in the real execution.

So I think what's being said is that a system is more linearizable the closer it is to representing the actual order of events. Not sure.

The CAP theorem, or impossibility, states that a distributed system can have at most two of three qualities: consistency, availability, and partition tolerance. It's called an impossibility because it says it's impossible to have all three.

Consistency is how closely the state of every node in the system reflects the state of every other node.

Availability is the ability of the every node to fulfill requests. A node is considered unavailable if it's operational but refusing requests.

Partition tolerance is the capacity of nodes to operate correctly even if messages between them are dropped. A _network partition_ is what happens when, through a point of failure in network, nodes are unable to communicate. Imagine having a server in the US and a server in London, and the network router in the London server fails. There is now a _partition_ between the London node and the US node (and any clients).

Next I need to read [Thoughts on the CAP Theorem](https://www.researchgate.net/publication/221343286_A_Certain_Freedom_Thoughts_on_the_CAP_Theorem)

#### Definition of _quiescent_:

> in a state or period of inactivity or dormancy.

They used the term "quiescent consistency," which I think just means that state consistency between nodes is designed to be intermittent.

> Note also that CRDTs are weaker than non-blocking constructs, which are generally based on a hardware consensus primitive.

They cite the book [_The Art of Multiprocessor Programming_](https://www.e-reading.club/bookreader.php/134637/Herlihy,_Shavit_-_The_art_of_multiprocessor_programming.pdf), by Nir Shavit. "Hardware consensus primitive" isn't a term I can just put into Google, so I'd have to do more research if I wanted to understand what was being said here. But Nir's book looks really interesting anyway. I thought it was about writing programs that run on distributed systems, but it looks like it's about multi-core programming, which could be a really valuable skill to learn.

They're going to do a shopping cart in an example later on. That sounds awesome.

> We consider a distributed system consisting of processes interconnected by an asynchronous network. The network can partition and recover, and nodes can operate in disconnected mode for some time. A process may crash and recover; its memory survives crashes. We assume non-byzantine behaviour.

"Byzantine" just looks like some kind of field jargon for "complex." Google's second definition (after "relating to Byzantium") is:

> (of a system or situation) excessively complicated, and typically involving a great deal of administrative detail.

They define "atoms" and "objects." Apparently atoms aren't mutated, but objects are. This seems like GraphQL's definition of objects and scalars, where objects are made up of some number of scalars. Not sure if this is the same thing, or a similar concept.

The identity, or content of an object is called its _payload_.