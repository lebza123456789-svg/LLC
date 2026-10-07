class User:
    def __init__(self, username, password, email, profile_picture=None):
        self.username = username
        self.password = password
        self.email = email
        self.profile_picture = profile_picture
    
    def create_acc(self):
        return f"{self.username} Account created succesfully"


    def login(self):
        return f"{self.username} Successfully logged in!"
    
    def logout(self):
        return f"{self.username} Successfully logged out"
    
    def add_car(self):
        pass
    
    def vote(self):
        pass
    
    def comment(self):
        pass

class Clan:
    def __init__(self, name, description, profile_pricture=None):
        self.name = name
        self.description = description
        self.profile_picture = profile_picture
    
    def create_clan(self):
        return f"self.name clan successfully created!"
    
    def create_event(self):
        pass
    
    def create_post(self):
        pass

class Car:
    def __init__(self, description, picture=None):
        self.description = description
        self.picture = picture
    
class Post:
    def __init__(self, content, picture=None):
        self.content = content
        self.picture = picture
    
    def create_post(self):
        pass
    
    def edit_post(self):
        pass
    
    def delete_post(self):
        pass
    

class Comment:
    def __init__(self, content):
        self.cotent = content
    
    def create_comment(self):
        pass
    
    def delete_comment(self):
        pass
    

   
class Events:
    def __init__(self, name, description, date, location, picture=None):
        self.name = name
        self.description = description 
        self.date = date 
        self.location = location
        self.picture = picture
    
    def edit_event():
        pass
    
    def delete_event(self):
        pass

class EventCompetitionResults:
    def __init__(self, position, category, score):
        self.position = position
        self.category = category
        self.score = score
    
    def add_result(self):
        pass
    
    def update_results(self):
        pass