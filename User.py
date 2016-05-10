class User:
    
    def __init__(self, id, surname, name, nickname, ranking, photo):
        self.id = id
        self.surname = surname
        self.name = name
        self.nickname = nickname
        self.ranking = ranking
        self.photo = photo
        
    def get_full_name(self):
        return self.surname+" "+self.name
        
    def get_photo(self):
        return self.photo