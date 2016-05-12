"""
This module is here to store data in database and make computation on it.
"""
from database import *

class User(db.Model):
    """ This class represent a user in data with some others attributes."""
    id_user = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(100))
    name = db.Column(db.String(100))
    nickname = db.Column(db.String(100), unique=True)
    photo = db.Column(db.String(200))

    def __init__(self, surname, name, nickname, photo):
        self.surname = surname
        self.name = name
        self.nickname = nickname
        self.photo = photo
        self.ranking = 1000
        self.number_of_match = 0

    def get_full_name(self):
        """ Return the full name of a user"""
        return self.surname+" "+self.name

    def get_name(self):
        """ Return the name of a user"""
        return self.name

    def get_photo(self):
        """ Return the photo of a user"""
        return self.photo

    def get_nickname(self):
        """ Return the nickname of a user"""
        return self.nickname

    def set_ranking(self, ranking):
        """ Set the ranking of a user"""
        self.ranking = ranking

    def get_ranking(self):
        """ Return the ranking of a user"""
        return self.ranking


class Match(db.Model):
    """This class represents a match in database."""
    id_match = db.Column(db.Integer, primary_key = True)
    date = db.Column(db.Date)
    score_e1 = db.Column(db.Integer)
    score_e2 = db.Column(db.Integer)
    user = db.relationship('User')
    player11 = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    player12 = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    player21 = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    player22 = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    
    
    
    

    def __init__(self, date, score_e1, score_e2, player11,
                 player12, player21, player22):
        self.date = date
        self.score_e1 = score_e1
        self.score_e2 = score_e2
        self.player11 = player11
        self.player12 = player12
        self.player21 = player21
        self.player22 = player22
