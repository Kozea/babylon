"""
This module is here to store data in database and make computation on it.
"""


class User:
    """ This class represent a user in data with some others attributes."""

    def __init__(self, id_user, surname, name, nickname, photo):
        self.id_user = id_user
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


class Match:
    """This class represents a match in database."""

    def __init__(self, id_match, date, score_e1, score_e2, player11,
                 player12, player21, player22):
        self.id_match = id_match
        self.date = date
        self.score_e1 = score_e1
        self.score_e2 = score_e2
        self.player11 = player11
        self.player12 = player12
        self.player21 = player21
        self.player22 = player22
