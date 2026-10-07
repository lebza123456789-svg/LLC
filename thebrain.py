from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class User:
    username: str
    email: str
    password_hash: str
    profile_picture: str | None = None
    cars: list["Car"] = field(default_factory=list)
    location: str | None = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Car:
    owner: User
    description: str
    picture: str | None = None
    ratings: list["Rating"] = field(default_factory=list)

    def average_rating(self):
        return sum(r.score for r in self.ratings) / len(self.ratings) if self.ratings else 0

@dataclass
class Rating:
    car: Car
    vote: User
    score: int

@dataclass
class Clan:
    name: str
    description: str
    owner: User
    profile_picture: str | None = None
    members: list[User] = field(default_factory=list)
    events: list["Event"] = field(default_factory=list)

@dataclass
class Event:
    clan: Clan
    name: str
    description: str
    date: datetime
    location: str
    picture: str | None = None
    results: list["EventResult"] = field(default_factory=list)

@dataclass
class EventResult:
    event: Event
    car: Car
    position: int
    score: int
    category: str
    resulted_at: datetime = field(default_factory=datetime.now)


@dataclass
class Post:
    author: User
    content: str
    picture: str | None = None
    comments: list["Comment"] = field(default_factory=list)
    posted_at: datetime = field(default_factory=datetime.now)


@dataclass
class Comment:
    post: Post
    user: User
    content: str
    created_at: datetime = field(default_factory=datetime.now)

def leaderboard(car: list[Car]):
    leaderboard_data = []
    for c in car:
        avg_rating = c.average_rating()
        leaderboard_data.append({
            "username": c.owner.username,
            "average_rating": avg_rating
        })

    leaderboard_data.sort(key=lambda x: x["average_rating"], reverse=True)

    return leaderboard_data

