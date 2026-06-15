# Beeworking MongoDB Build — Checklist

Tracking progress against `beeworking_mongodb_prompt.md`.

## Prerequisites
- [x] MongoDB running locally — **YES**: service "MongoDB Server (MongoDB)" Running, port 27017 listening, Server v8.3
- [x] `mongosh` available — **YES**: installed v2.8.3 (user-authorized) at `C:\Users\santi\AppData\Local\Programs\mongosh\mongosh.exe`; `ping: ok`
- [x] Confirm `beeworking` DB does NOT already exist — **CONFIRMED ABSENT**: existing DBs = Mena_DB, admin, config, local; `beeworking` has 0 collections. `Mena_DB` left untouched.

## Build steps  (script: `build_beeworking.js`)
- [x] Create `beeworking` database
- [x] Create collection `Users` (with JSON schema validator)
- [x] Create collection `Badges` (with JSON schema validator)
- [x] Create collection `Events` (with JSON schema validator)
- [x] Create collection `Achievements` (with JSON schema validator)
- [x] Create collection `Assistence` (with JSON schema validator)

## Indexes
- [x] `Users.email` (unique)
- [x] `Users.username` (unique)
- [x] `Events.badges_id`
- [x] `Achievements.events_id`
- [x] `Achievements.users_id`
- [x] `Assistence.users_id`
- [x] `Assistence.badges_id`
- [x] `Assistence.events_id`

## Sample data (one document per collection, valid ObjectId refs)
- [x] Users sample        — `_id` …c114
- [x] Badges sample       — `_id` …c115
- [x] Events sample       — `_id` …c116, badges_id → …c115
- [x] Achievements sample — `_id` …c117, events_id → …c116, users_id → …c114
- [x] Assistence sample   — `_id` …c118, users_id → …c114, badges_id → …c115, events_id → …c116

## Verification  (script: `verify_beeworking.js`)
- [x] List databases — beeworking present (Mena_DB untouched)
- [x] List collections in `beeworking` — all 5 present
- [x] Print one document from each collection — all printed, refs consistent

## Notes / observations
- Built exactly as specified — no schema changes, no extra collections/fields/indexes.
- **`Badges.event_name` (string)** looks redundant: the same event name is also held in
  `Events.name`, and `Events.badges_id` already links the two. The diagram has Badges point
  to an event by *name string* rather than by an `events_id` ObjectId reference. Kept as-is
  per instructions (not "corrected"), flagging it as requested.
- Validators mark all listed fields as `required` with the diagram's `bsonType`
  (`objectId` for `*_id`, `date` for date fields, else `string`). `additionalProperties`
  left at default (permissive) — no extra restriction added beyond what was specified.
- mongosh was installed with explicit user authorization (v2.8.3). MongoDB server v8.3 was
  already running. No system config altered.
