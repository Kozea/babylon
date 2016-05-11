class User:

    def __init__(self, id, surname, name, nickname, photo):
        self.id = id
        self.surname = surname
        self.name = name
        self.nickname = nickname
        self.photo = photo
        self.ranking = 1000
        self.number_of_match = 0

    def get_full_name(self):
        return self.surname+" "+self.name

    def get_photo(self):
        return self.photo

    def get_nickname(self):
        return self.nickname

    def set_ranking(self, ranking):
        self.ranking = ranking