import sqlite3

connection = sqlite3.connect("llc")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL,
email TEXT NOT NULL,
password_hash TEXT NOT NULL,
profile_picture TEXT,
location Text,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
 """)

cursor.execute("""
CREATE TABLE IF NOT EXISTS cars (
id INTEGER PRIMARY KEY AUTOINCREMENT,
owner_id INTEGER NOT NULL,
description TEXT NOT NULL,
picture TEXT,
FOREIGN KEY (owner_id) REFERENCES users(id)
)
 """)

cursor.execute("""
CREATE TABLE IF NOT EXISTS ratings (
id INTEGER PRIMARY KEY AUTOINCREMENT,
car_id INTEGER NOT NULL,
vote_id INTEGER NOT NULL,
score INTEGER NOT NULL,
FOREIGN KEY (car_id) REFERENCES cars(id),
FOREIGN KEY (vote_id) REFERENCES users(id),
UNIQUE (car_id, vote_id)

)
 """)

cursor.execute("""
CREATE TABLE IF NOT EXISTS clans(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name text NOT NULL,
description text NOT NULL,
owner_id INTEGER NOT NULL,
profile_picture text,
FOREIGN KEY (owner_id) REFERENCES users(id),
UNIQUE (NAME)
)
 """)

cursor.execute("""
CREATE TABLE IF NOT EXISTS clan_members(
id INTEGER PRIMARY KEY AUTOINCREMENT,
clan_id INTERGER NOT NULL,
user_id INTEGER NOT NULL,
FOREIGN KEY (clan_id) REFERENCES clans(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS events(
id INTEGER PRIMARY KEY AUTOINCREMENT,
clan_id INTEGER NOT NULL,
name TEXT NOT NULL,
description TEXT NOT NULL,
date TIMESTAMP NOT NULL,
location TEXT NOT NULL, 
picture TEXT,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (clan_id) REFERENCES clans(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS event_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    car_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    score INTEGER NOT NULL,
    category TEXT NOT NULL,
    resulted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (car_id) REFERENCES cars(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS posts (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
clan_id INTEGER,
content TEXT NOT NULL,
picture TEXT,
posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (user_id) REFERENCES users(id),
FOREIGN KEY (clan_id) REFERENCES clans(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS comments(
id INTEGER PRIMARY KEY AUTOINCREMENT,
post_id INTEGER NOT NULL,
user_id INTEGER NOT NULL,
content TEXT NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (post_id) REFERENCES posts(id)
FOREIGN KEY (user_id) REFERENCES users(id)
)
""")
