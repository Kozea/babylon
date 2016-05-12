"""
This module is here to store data in database and make computation on it.
"""
from database import *

class Match(db.Model):
    """This class represents a match in database."""
    id_match = db.Column(db.Integer, primary_key = True)
    date = db.Column(db.Date)
    score_e1 = db.Column(db.Integer)
    score_e2 = db.Column(db.Integer)
    player11_id = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    player11 = db.relationship('User', foreign_keys=[player11_id])
    player12_id = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    player12 = db.relationship('User', foreign_keys=[player12_id])
    player21_id = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    player21 = db.relationship('User', foreign_keys=[player21_id])
    player22_id = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    player22 = db.relationship('User', foreign_keys=[player22_id])
    

class User(db.Model):
    """ This class represent a user in data with some others attributes."""
    id_user = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(100))
    name = db.Column(db.String(100))
    nickname = db.Column(db.String(100), unique=True)
    photo = db.Column(db.String(200))


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
    
    def set_number_of_matchs(self):
        self.number_of_match = 0

    def get_ranking(self):
        """ Return the ranking of a user"""
        return self.ranking
