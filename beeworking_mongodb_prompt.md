# Beeworking — MongoDB Database Build Instructions

> Hand this whole file to Claude Code. It contains both the exact schema to build
> and the instructions for how to build it.

---

## Role of the AI

You are a database engineer with terminal access to my machine. You can run shell
commands and use `mongosh` to connect to my local MongoDB instance. You build
exactly what the specification below describes — nothing more, nothing less.

## Objective

Create a MongoDB database named **`beeworking`** containing the **5 collections**
defined in the schema below. Set up each collection with the correct fields,
appropriate data types, and indexes on the foreign-key reference fields. The schema
is fixed and comes from a hand-drawn database diagram — reproduce it faithfully.

## Procedure

1. Verify MongoDB is running locally and that `mongosh` is available. If it is not
   running or not installed, stop and tell me before doing anything else.
2. Connect to the local MongoDB instance with `mongosh`.
3. Create the `beeworking` database.
4. Create each of the 5 collections listed in the schema below, in this order:
   `Users`, `Badges`, `Events`, `Achievements`, `Assistence`.
5. For each collection, apply a JSON schema validator matching the fields and types
   defined below so documents are validated on insert.
6. Create indexes on every foreign-key reference field (the `*_id` fields) and on
   `Users.email` and `Users.username` (unique).
7. Insert **one sample document** per collection so I can confirm the structure
   works. Use realistic placeholder values and valid `ObjectId` references between
   related collections.
8. When finished, run a short verification: list the databases, list the
   collections in `beeworking`, and print one document from each collection.
9. Report back exactly what you created.

## Limits

- **Do not change the schema.** Use only the collections, fields, and types listed
  below. Do not rename, add, remove, split, or merge any field or collection.
- **Do not add new collections, fields, indexes, or features** that are not
  described in this document, even if you think they would improve the design.
- **Do not modify or "correct" the diagram.** If something looks unusual (for
  example, a field that seems redundant), keep it as written and mention it to me
  instead of fixing it yourself.
- **Do not touch any other database** on the MongoDB instance. Only create and
  write to `beeworking`.
- **Do not drop, delete, or overwrite** any existing data. If a `beeworking`
  database already exists, stop and ask me before continuing.
- **Do not install software, change MongoDB config, or alter system files.** If a
  prerequisite is missing, tell me — do not fix it on your own.
- **Do not run destructive commands** (`dropDatabase`, `drop`, mass deletes)
  without explicit confirmation from me first.

---

## Schema (the diagram, in text form)

`_id` is the MongoDB primary key (auto-generated `ObjectId`). Fields ending in
`_id` are references (foreign keys) to another collection's `_id`.

### Users
| Field          | Type      | Notes                          |
|----------------|-----------|--------------------------------|
| `_id`          | ObjectId  | Primary key                    |
| `username`     | string    | Unique                         |
| `password`     | string    | Stored hashed                  |
| `email`        | string    | Unique                         |
| `rol`          | string    | User role                      |
| `verification` | string    | Verification status / token    |
| `name`         | string    | First name                     |
| `lastname`     | string    | Last name                      |

### Badges
| Field         | Type     | Notes                |
|---------------|----------|----------------------|
| `_id`         | ObjectId | Primary key          |
| `event_name`  | string   | Name of the event    |
| `name`        | string   | Badge name           |
| `description` | string   | Badge description    |
| `image`       | string   | Image URL or path    |
| `token`       | string   | Badge token          |
| `date`        | date     | Date issued          |
| `qr`          | string   | QR code value        |

### Events
| Field         | Type     | Notes                          |
|---------------|----------|--------------------------------|
| `_id`         | ObjectId | Primary key                    |
| `name`        | string   | Event name                     |
| `description` | string   | Event description              |
| `date`        | date     | Event date                     |
| `prize`       | string   | Prize for the event            |
| `badges_id`   | ObjectId | Reference → `Badges._id`       |

### Achievements
| Field        | Type     | Notes                          |
|--------------|----------|--------------------------------|
| `_id`        | ObjectId | Primary key                    |
| `events_id`  | ObjectId | Reference → `Events._id`       |
| `users_id`   | ObjectId | Reference → `Users._id`        |
| `date`       | date     | Date earned                    |
| `prize`      | string   | Prize earned                   |

### Assistence
| Field        | Type     | Notes                          |
|--------------|----------|--------------------------------|
| `_id`        | ObjectId | Primary key                    |
| `users_id`   | ObjectId | Reference → `Users._id`        |
| `badges_id`  | ObjectId | Reference → `Badges._id`       |
| `events_id`  | ObjectId | Reference → `Events._id`       |

### Relationships
- `Events.badges_id` → `Badges._id` (each event links to one badge)
- `Assistence` joins `Users`, `Badges`, and `Events` (attendance record)
- `Achievements` joins `Users` and `Events` (prize record)
