class User:
    def __init__(self, username, name, surname, password, email, profile_picture=None):
        self.username = username
        self.name = name
        self.surname = surname
        self.password = password
        self.email = email
        self.profile_picture = profile_picture

    def save_to_database(self, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO users (username, name, surname, password, email, profile_picture) VALUES (?, ?, ?, ?, ?, ?)", (self.username, self.name, self.surname, self.password, self.email, self.profile_picture))

class Events:
    def  __init__(self, title, description, date, time, location, category, poster, username):
        self.title = title 
        self.description = description 
        self.date = date
        self.time = time
        self.location = location
        self.category = category
        self.poster = poster
        self.username = username

    def save_events(self, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO events (title, description, date, time, location, category, poster, username) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (self.title, self.description, self.date, self.time, self.location, self.category, self.poster, self.username))

    def get_events_by_location(self, db_connection, location):
        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM events WHERE location = ?", (location,))
        return cursor.fetchall()

    def get_events_by_category(self, db_connection, category):
        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM events WHERE category = ?", (category,))
        return cursor.fetchall()
    