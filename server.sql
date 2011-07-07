CREATE TABLE workstations (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE terminals (
    id INTEGER PRIMARY KEY,
    name TEXT,
    workstation_id INTEGER,
    FOREIGN KEY(workstation_id) REFERENCES workstations(id)
);
