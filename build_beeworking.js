// Beeworking database build script.
//   Local:  mongosh beeworking build_beeworking.js
//   Atlas:  mongosh "<your-atlas-uri>" build_beeworking.js
//
// Builds exactly the 5 collections from beeworking_mongodb_prompt.md: validators,
// indexes on *_id reference fields + unique Users.email/username, and one sample
// document each. Safe to re-run (idempotent): collections/validators are created or
// updated in place, createIndex is a no-op if the index already exists, and sample
// docs are upserted on a natural key so re-running never duplicates or drops data.

const dbx = db.getSiblingDB("beeworking");

// Field/validator definitions — the fixed schema from the spec.
const SCHEMAS = {
  Users: {
    required: ["username", "password", "email", "rol", "verification", "name", "lastname"],
    properties: {
      username:     { bsonType: "string" },
      password:     { bsonType: "string" },
      email:        { bsonType: "string" },
      rol:          { bsonType: "string" },
      verification: { bsonType: "string" },
      name:         { bsonType: "string" },
      lastname:     { bsonType: "string" }
    }
  },
  Badges: {
    required: ["event_name", "name", "description", "image", "token", "date", "qr"],
    properties: {
      event_name:  { bsonType: "string" },
      name:        { bsonType: "string" },
      description: { bsonType: "string" },
      image:       { bsonType: "string" },
      token:       { bsonType: "string" },
      date:        { bsonType: "date" },
      qr:          { bsonType: "string" }
    }
  },
  Events: {
    required: ["name", "description", "date", "prize", "badges_id"],
    properties: {
      name:        { bsonType: "string" },
      description: { bsonType: "string" },
      date:        { bsonType: "date" },
      prize:       { bsonType: "string" },
      badges_id:   { bsonType: "objectId" }
    }
  },
  Achievements: {
    required: ["events_id", "users_id", "date", "prize"],
    properties: {
      events_id: { bsonType: "objectId" },
      users_id:  { bsonType: "objectId" },
      date:      { bsonType: "date" },
      prize:     { bsonType: "string" }
    }
  },
  Assistence: {
    required: ["users_id", "badges_id", "events_id"],
    properties: {
      users_id:  { bsonType: "objectId" },
      badges_id: { bsonType: "objectId" },
      events_id: { bsonType: "objectId" }
    }
  }
};

// ---------------------------------------------------------------------------
// 1) Collections + JSON schema validators (created or updated in place)
// ---------------------------------------------------------------------------
const ORDER = ["Users", "Badges", "Events", "Achievements", "Assistence"];
const existing = new Set(dbx.getCollectionNames());

ORDER.forEach(name => {
  const validator = { $jsonSchema: { bsonType: "object", required: SCHEMAS[name].required, properties: SCHEMAS[name].properties } };
  if (existing.has(name)) {
    dbx.runCommand({ collMod: name, validator: validator });   // update validator, keep data
    print("Validator updated: " + name);
  } else {
    dbx.createCollection(name, { validator: validator });
    print("Collection created: " + name);
  }
});

// ---------------------------------------------------------------------------
// 2) Indexes — on every *_id reference field + unique Users.email/username
//    createIndex is idempotent: a no-op when the index already exists.
// ---------------------------------------------------------------------------
dbx.Users.createIndex({ email: 1 }, { unique: true });
dbx.Users.createIndex({ username: 1 }, { unique: true });

dbx.Events.createIndex({ badges_id: 1 });

dbx.Achievements.createIndex({ events_id: 1 });
dbx.Achievements.createIndex({ users_id: 1 });

dbx.Assistence.createIndex({ users_id: 1 });
dbx.Assistence.createIndex({ badges_id: 1 });
dbx.Assistence.createIndex({ events_id: 1 });

print("Indexes ensured.");

// ---------------------------------------------------------------------------
// 3) One sample document per collection, with valid ObjectId references.
//    Upserted on a natural key so re-running neither duplicates nor overwrites.
// ---------------------------------------------------------------------------
function ensure(coll, filter, doc) {
  dbx.getCollection(coll).updateOne(filter, { $setOnInsert: doc }, { upsert: true });
  return dbx.getCollection(coll).findOne(filter)._id;
}

const userId = ensure("Users", { email: "jane.doe@example.com" }, {
  username:     "jdoe",
  password:     "$2b$12$Q8wErTyUiOpAsDfGhJkLmO0pQrStUvWxYz1234567890abcdef",
  email:        "jane.doe@example.com",
  rol:          "member",
  verification: "verified",
  name:         "Jane",
  lastname:     "Doe"
});

const badgeId = ensure("Badges", { token: "BADGE-7F3A9C2E" }, {
  event_name:  "Hackathon 2026",
  name:        "First Place",
  description: "Awarded to the winning team of Hackathon 2026.",
  image:       "https://cdn.beeworking.example/badges/first-place.png",
  token:       "BADGE-7F3A9C2E",
  date:        new Date("2026-06-11T00:00:00Z"),
  qr:          "https://beeworking.example/verify/BADGE-7F3A9C2E"
});

const eventId = ensure("Events", { name: "Hackathon 2026" }, {
  name:        "Hackathon 2026",
  description: "Annual 48-hour internal hackathon.",
  date:        new Date("2026-06-11T09:00:00Z"),
  prize:       "$5,000 team prize",
  badges_id:   badgeId
});

const achievementId = ensure("Achievements", { events_id: eventId, users_id: userId }, {
  events_id: eventId,
  users_id:  userId,
  date:      new Date("2026-06-11T18:00:00Z"),
  prize:     "$5,000 team prize"
});

const assistenceId = ensure("Assistence", { users_id: userId, events_id: eventId }, {
  users_id:  userId,
  badges_id: badgeId,
  events_id: eventId
});

print("Sample docs ensured:");
print("  Users._id        = " + userId);
print("  Badges._id       = " + badgeId);
print("  Events._id       = " + eventId);
print("  Achievements._id = " + achievementId);
print("  Assistence._id   = " + assistenceId);
print("Done. Collections: " + JSON.stringify(dbx.getCollectionNames()));
