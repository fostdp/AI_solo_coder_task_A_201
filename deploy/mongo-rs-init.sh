#!/bin/bash

set -e

echo "Waiting for MongoDB to start..."
sleep 10

echo "Initializing MongoDB Replica Set..."

mongosh --host mongodb:27017 <<EOF
  rs.initiate({
    _id: "rs0",
    version: 1,
    members: [
      { _id: 0, host: "mongodb:27017", priority: 1 }
    ]
  });
EOF

echo "Waiting for replica set to become ready..."
sleep 5

echo "Creating database and indexes..."
mongosh --host mongodb:27017 <<EOF
  use lost_wax_casting;

  db.createCollection("castings");
  db.createCollection("sensors");
  db.createCollection("simulations");
  db.createCollection("defects");
  db.createCollection("alerts");

  db.castings.createIndex({ created_at: -1 });
  db.sensors.createIndex({ casting_id: 1, timestamp: -1 });
  db.simulations.createIndex({ casting_id: 1, step_number: 1 });
  db.defects.createIndex({ casting_id: 1, severity: 1 });
  db.alerts.createIndex({ casting_id: 1, acknowledged: 1, created_at: -1 });

  print("Database initialized successfully!");
EOF

echo "MongoDB Replica Set initialized!"
