const dbName = "lost_wax_casting";

db = db.getSiblingDB(dbName);

print("=== Initializing Lost Wax Casting Simulation Database ===");

const collections = [
    {
        name: "castings",
        indexes: [{ key: { created_at: -1 }, name: "created_at_-1" }],
    },
    {
        name: "sensors",
        indexes: [
            { key: { casting_id: 1, timestamp: -1 }, name: "casting_id_1_timestamp_-1" },
            { key: { timestamp: 1 }, name: "timestamp_1", expireAfterSeconds: 2592000 },
        ],
    },
    {
        name: "simulations",
        indexes: [
            { key: { casting_id: 1, step_number: 1 }, name: "casting_id_1_step_number_1", unique: true },
        ],
    },
    {
        name: "defects",
        indexes: [{ key: { casting_id: 1, severity: 1 }, name: "casting_id_1_severity_1" }],
    },
    {
        name: "alerts",
        indexes: [
            {
                key: { casting_id: 1, acknowledged: 1, created_at: -1 },
                name: "casting_id_1_acknowledged_1_created_at_-1",
            },
        ],
    },
];

collections.forEach((col) => {
    if (!db.getCollectionNames().includes(col.name)) {
        db.createCollection(col.name);
        print(`Created collection: ${col.name}`);
    } else {
        print(`Collection already exists: ${col.name}`);
    }
    const collection = db.getCollection(col.name);
    const existingIndexes = collection.getIndexes().map((i) => i.name);
    col.indexes.forEach((idx) => {
        if (!existingIndexes.includes(idx.name)) {
            const options = { name: idx.name };
            if (idx.expireAfterSeconds !== undefined) {
                options.expireAfterSeconds = idx.expireAfterSeconds;
            }
            if (idx.unique) {
                options.unique = true;
            }
            collection.createIndex(idx.key, options);
            print(`  Created index: ${idx.name}`);
        } else {
            print(`  Index already exists: ${idx.name}`);
        }
    });
});

print("=== Sample Data Initialization ===");

const castingId = "sample-zunpan-001";
if (db.castings.countDocuments({ id: castingId }) === 0) {
    db.castings.insertOne({
        id: castingId,
        name: "曾侯乙尊盘复原实验 #001",
        status: "idle",
        created_at: new Date(),
        completed_at: null,
        parameters: {
            material: "青铜 (Cu-Sn-Pb)",
            pouring_temperature_target: 1180,
            wax_pattern_temperature: 60,
            shell_layers: 9,
            shell_material: "硅溶胶+石英砂",
            expected_casting_time: 60,
        },
    });
    print(`Inserted sample casting: ${castingId}`);
} else {
    print(`Sample casting already exists: ${castingId}`);
}

const now = new Date();
const baseTime = now.getTime() - 10 * 60 * 1000;
const existingSensorCount = db.sensors.countDocuments({ casting_id: castingId });
if (existingSensorCount === 0) {
    const sensorData = [];
    for (let i = 0; i < 10; i++) {
        sensorData.push({
            id: `sample-sensor-${i}`,
            casting_id: castingId,
            timestamp: new Date(baseTime + i * 60 * 1000),
            wax_temperature: 55 + i * 3 + Math.random() * 5,
            pouring_temperature: 1150 + Math.random() * 50,
            shell_permeability: 40 + Math.random() * 20,
            filling_progress: Math.min(100, i * 10 + Math.random() * 5),
        });
    }
    db.sensors.insertMany(sensorData);
    print(`Inserted ${sensorData.length} sample sensor records`);
}

print("\n=== Database initialization complete ===");
print(`Database: ${dbName}`);
print(`Collections: ${db.getCollectionNames().join(", ")}`);
