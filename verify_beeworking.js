// Verification — run with: mongosh beeworking verify_beeworking.js
print("=== Databases ===");
db.adminCommand({ listDatabases: 1 }).databases.forEach(d => print("  " + d.name));

print("\n=== Collections in beeworking ===");
db.getCollectionNames().sort().forEach(c => print("  " + c));

["Users", "Badges", "Events", "Achievements", "Assistence"].forEach(c => {
  print("\n=== " + c + " : sample document ===");
  printjson(db.getCollection(c).findOne());
  print("--- indexes on " + c + " ---");
  db.getCollection(c).getIndexes().forEach(i =>
    print("  " + i.name + "  " + JSON.stringify(i.key) + (i.unique ? "  [unique]" : ""))
  );
});
