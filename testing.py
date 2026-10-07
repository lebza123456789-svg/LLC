from thebrain import User, Car, Rating, leaderboard
from datetime import datetime

user1 = User(
    username="jack",
    email="jack@example.com",
    password_hash="hashed_password_1",
    profile_picture=None,
    location="Bloemfontein",
    created_at=datetime.now()

)

user2 = User(
    username="Ray",
    email="Ray@example.com",
    password_hash="hashed_password_3",
    profile_picture=None,
    location="welkom",
    created_at=datetime.now()

)

car1 = Car(
    owner= user1,
    description="bagged"
)

user1.cars.append(car1)

rating1 = Rating(
    car=car1,
    vote=user2,
    score=8
)

rating2 = Rating(
    car=car1,
    vote=user1,
    score=7.5
)

car1.ratings.append(rating1)
car1.ratings.append(rating2)

print(car1.average_rating())