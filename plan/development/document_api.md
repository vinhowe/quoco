# Document API proposal

## Features

### History

The document API should provide a way to access documents at different points in history. The flat state of a document at any point in time can be retrieved by computing the result of stored transformation deltas either from the beginning of the document's history or from the last flat snapshot.

### Live editing (post-MVP)

This will be delayed until a later release. I'll start with a basic locking model, where every editor who attempts to modify the document will have to secure a lock from the server, along with the latest contents of the document. This means that only one client will be able to access a document at a time, and this is fine, for now.

I want to implement some kind of CRDT. Maybe like [automerge](https://github.com/automerge/automerge/blob/master/frontend/index.js), whose `Automerge.Text` looks promising, although it says it's experimental.

It may also be worth attempting to make my own implementation.

Implementations:
* [Atom Teletype CRDT](https://github.com/atom/teletype-crdt/blob/master)
* Xi editor

Papers:
* [Data consistency for P2P Collaborative Editing](https://doi.org/10.1145/1180875.1180916)
* [Supporting String-Wise Operations and Selective Undo for Peer-to-Peer Group Editing](https://doi.org/10.1145/2660398.2660401)
* [High Responsiveness for Group Editing CRDTs](https://doi.org/10.1145/2957276.2957300)

IMPORTANT TO NOTE: If we're going to allow documents to be edited by text editors that don't support downstream updates (like vs code, vi, the terminal perora client, or any other file-based editor), then documents will need to have special locking functionality. A editor without realtime capabilities will need to lock the document, preventing any realtime editors from modifying it for the duration of the lock. On the other hand, if any realtime editors are modifying the document, the document will have a "realtime lock," and any non-realtime editors will be unable to edit the document until the lock is released (either manually or after a timeout).

### Contextual add-ins

* Tags
* References to other documents (but not all documents, need some kind of document space partitioning, like a namespace of some sort, for swap space text and principle names/bodies/comments)
* References to quotes from other documents
* Live references to existing objects, like:
    * Principles, with the current title and body
    * Objectives, with days until due
* Creating and referencing objects inline:
    * Questions I want to answer later, and the answers when I find them (this sounds a lot like research sessions)

### Quotes

When a quote is taken from a document, it should reference the state of the document at that point in time. Additionally, it should contain
a rough draft of how the schema of a quote object might look:

```
Quote:
    id: ID
    document: DocumentRef
    start: Int
    end: int
    # I don't know how the value should actually be stored, but
    # it seems like a bad idea to load a document and take the
    # quoted section from it every time a quote is referenced
    value: String (or something else)
```

An additional concern is if/how quoting is handled for use cases where a document is being referenced by something like a principle or a swap space item. If the title of a principle can be quoted, then the quote should end up linking to the principle instead of the document. Documents should be opened in their referenced environments, although this is difficult to define.

Maybe this calls for a resolver for readable user-facing IDs. The document schema could have an optional `reference` parameter that would point to the referring resource (like a principle or swap item). When a user attempted to go to the source of a quote, the system would first search for the `reference` parameter and attempt to load it. If it either didn't exist or failed to resolve, the client would attempt to open the document with the configured editor.

This also makes sense for references from within documents. A principle could be referenced like `!P123` (not sure about this syntax) in a document, which could be replaced with live information about the principle when displayed for the client.

### Cache for references and queries

There needs to be some kind of caching so that we can do full text search on fields of objects that reference documents. An example might be:

```
Principle:
    name: (DocumentRef)
    body: (DocumentRef)
    id: ID!
    
```

It's much more difficult to index and run full text searches on principles if you have to query the connected document every time.

## Schema

### MVP

```yaml #graphql
# All references to other objects are stored as ID lists in the database

type Document {
    id: ID!
    # Updated through a transaction whenever a DocumentVersion is added
    body: String
    createdAt: DateTime!
    # Updated through a transaction whenever a DocumentVersion is added
    # It's more efficient to store the current version number here so we don't have to query the current DocumentVersion
    currentVersionNumber: Int!
    # Updated through a transaction whenever a DocumentVersion is added
    currentVersion: DocumentVersion!
    # Updated through a transaction whenever a DocumentVersion is added
    versions: [DocumentVersionConnection]! 
}

# Treated as immutable
type DocumentVersion {
    id: ID!
    createdAt: DateTime!
    versionNumber: Int!
    document: Document!
    body: String
}

type DocumentVersionEdge {
    node: DocumentVersion!
    cursor: String!
}

type DocumentVersionConnection {
    edges: [DocumentVersionEdge]!
    nodes: [DocumentVersion]!
    # !!! And whatever else a connection has
}

# Treated as immutable
'''
Selection of text from a document
'''
type Quote {
    id: ID!
    document: Document!
    version: DocumentVersion!
    createdAt: DateTime!
    '''
    Start position of quote in number of characters from beginning of body of referenced document version
    '''
    position: Int!
    '''
    Length of quote in number of characters
    '''
    length: Int! (calculated whenever body is created/updated)
    body: String!
}

# I think it's a good idea to separate quotations and experiences, but my concern is that if an underlying quote is somehow changed, then the experience isn't the same. Should quotes be immutable? Yes. In order for the experience to be changed, a new quote should have to be selected, with the starting point being the last quote. It shouldn't be possible for the end user to modify an existing quote object.
type Experience {
    id: ID!
    createdAt: DateTime!
    quote: Quote!
}
```

### After MVP

Every document has a configuration. This describes what features can be used within it.
* Live information for inline references (like principles or objectives)
* Max length
* Max history (flat snapshot before history)

```yaml #graphql

type DocumentVersion {
    ...
    # Automatically generated whenever document is saved
    references: [DocumentReferenceItems]!
}

type Document {
    ...
    # References from current version
    references: [DocumentReferenceItems]!
}

# Quote is a reference to another
union DocumentReferenceItem = Issue | Principle | System | Quote | Document

# Client session is not unique to the document API, but is an important dependency
type ClientSession {
    id: ID # Or token
    startedAt: DateTime
    # When I do auth, I should add an expiry date field here
}
```

### Document lock process (post-MVP)

Server requires 5 seconds between lock changes, so it records `lockStart` field for Document object.

This requires that a Document have two fields:

* `clientLockId`
* `lockStart`

Process

* Client (with session id) requests lock on document
* Server revokes lock for any other clients
* Server sends newest version of document to client
* Client can send updates upstream until lock is revoked

### Client session details (post-MVP)

Every time a perora client session is created, it should request a session ID through a GraphQL mutation like `createSession`. The server should store a `ClientSession` object:

```yaml #graphql
ClientSession:
    id: ID # Or token
    startedAt: DateTime
    # When I do auth, I should have an expiry date
```

This should be used for obtaining locks on documents.

## Implementation

### Client

Haven't clarified how the client will interact with documents. It's possible that what I'll do is have a "document connection" concept.

For example, take a journal client. The client will request a new journal entry if none exists for that day. The server schema might look like this:

```graphql

type Query {
    # XOR
    '''
    journalEntry must be queried with either date or id, not both
    '''
    journalEntry(date: DateTime!, id: ID!): JournalEntry
}

type Mutation {
    updateDocument(id: ID, body: String): DocumentUpdateResponse
}

type DocumentUpdateResponse implements SomeResponseType {
    # however we respond here
}

type JournalEntry {
    id: ID!
    document: Document!
    createdAt: DateTime!
}

...

```

And the query might look like this:

```
query GetJournalEntry($date: DateTime!) {
    journalEntry(date: $date) {
        id
        document {
            id
            currentVersion {
                versionNumber
                body
            }
        }
    }
}
```

The update mutation would look like this:

```graphql
mutation UpdateDocument($id: ID!, $body: String) {
    updateDocument(id: $id, body: $body) {
        # response parameters
    }
}
```

The client would then interact with `document`.