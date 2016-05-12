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
