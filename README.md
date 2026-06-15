# TokenTeamW

# Beeworking — MongoDB Database

The `beeworking` database has **5 collections**: `Users`, `Badges`, `Events`,
`Achievements`, `Assistence`. The schema is defined in
[`beeworking_mongodb_prompt.md`](beeworking_mongodb_prompt.md) and built by the
scripts in this repo.

> The repo holds the **build scripts**, not the data. The live data lives in a
> MongoDB instance (local or, for shared use, MongoDB Atlas).

## Scripts
| File | Purpose |
|------|---------|
| `build_beeworking.js`  | Creates collections, validators, indexes, and one sample doc each. **Idempotent** — safe to re-run. |
| `verify_beeworking.js` | Lists databases/collections and prints a sample doc + indexes from each collection. |

Both target the `beeworking` database explicitly, so they run unchanged against a
local instance or Atlas.

## Run against a local MongoDB
```bash
mongosh beeworking build_beeworking.js
mongosh beeworking verify_beeworking.js
```

## Share via MongoDB Atlas (recommended for multiple users)
Set up the cluster once, load the schema, then hand out the connection string —
teammates connect directly, no repo clone or local MongoDB needed.

1. Create a free **M0** cluster at https://cloud.mongodb.com.
2. **Database Access** → add a user with `readWrite` on `beeworking`
   (give each person their own user/password).
3. **Network Access** → add each user's IP (or `0.0.0.0/0` for open access —
   only safe with strong per-user passwords).
4. **Connect → Drivers** → copy the connection string.
5. Copy `.env.example` to `.env`, paste your string into `ATLAS_URI`, and replace
   `<db_password>` with the real password. (`.env` is gitignored.)
6. Load the schema into Atlas (run once):

   **PowerShell (Windows)**
   ```powershell
   $env:ATLAS_URI = "mongodb://USER:PASSWORD@...your-atlas-hosts.../?ssl=true&replicaSet=...&authSource=admin"
   mongosh $env:ATLAS_URI build_beeworking.js
   mongosh $env:ATLAS_URI verify_beeworking.js
   ```

   **bash/zsh (macOS/Linux)**
   ```bash
   export ATLAS_URI="mongodb://USER:PASSWORD@...your-atlas-hosts.../?ssl=true&replicaSet=...&authSource=admin"
   mongosh "$ATLAS_URI" build_beeworking.js
   mongosh "$ATLAS_URI" verify_beeworking.js
   ```
7. Share the connection string + database name (`beeworking`) with users through a
   private channel.

## How to connect (for teammates)
You need two things: the **connection string** and the database name **`beeworking`**.
Replace `<password>` with your own database-user password, and keep the string private.

```
mongodb+srv://<user>:<password>@tokenteam.h9qviqr.mongodb.net/beeworking?appName=TokenTeam
```

### mongosh (shell)
```bash
mongosh "mongodb+srv://<user>:<password>@tokenteam.h9qviqr.mongodb.net/beeworking?appName=TokenTeam"
```

### MongoDB Compass (GUI)
Paste the same connection string into the "New Connection" box and click **Connect**,
then open the `beeworking` database.

### Node.js (`npm install mongodb`)
```js
const { MongoClient } = require("mongodb");

const client = new MongoClient(process.env.ATLAS_URI); // set ATLAS_URI in your environment
await client.connect();
const db = client.db("beeworking");

const users = await db.collection("Users").find().toArray();
console.log(users);

await client.close();
```

### Python (`pip install pymongo`)
```python
import os
from pymongo import MongoClient

client = MongoClient(os.environ["ATLAS_URI"])  # set ATLAS_URI in your environment
db = client["beeworking"]

for user in db["Users"].find():
    print(user)
```

> Load credentials from an environment variable / `.env` file (see `.env.example`).
> Never hard-code the password in source you commit. If the connection times out,
> make sure your IP is allowed in Atlas → Network Access.

## Security
- **Never commit** a connection string containing a real password. Keep it in
  `.env` (gitignored) and share it privately.
- Prefer **per-user** Atlas accounts over one shared password — easier to revoke.

## Notes
- `Badges.event_name` is redundant with `Events.name` (the two are also linked via
  `Events.badges_id`). Kept as-is to match the original diagram.
