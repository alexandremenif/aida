
-- Table creation for persons
CREATE TABLE IF NOT EXISTS persons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);

-- Table creation for events
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  start DATETIME NOT NULL,
  end DATETIME NOT NULL,
  CHECK (start < end)
);

-- Table creation for event_attendees
CREATE TABLE IF NOT EXISTS event_attendees (
  event_id INTEGER NOT NULL,
  person_id INTEGER NOT NULL,
  PRIMARY KEY (event_id, person_id),
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
);
