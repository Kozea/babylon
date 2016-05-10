import User

class Team:
    
    def __init__(self, id, player1, player2, name):
        self.id = id
        self.player1 = player1
        self.player2 = player2
        self.name = name
        
    def get_player1_name(self):
        return self.player1.get_full_name()
        
    def get_player2_name(self):
        if(self.player2 is None):
            return None
        return self.player2.get_full_name()
        
    def get_team_name(self):
        if(self.name is not None):
            return self.name
        return None
            
    def get_photo_player1(self):
        return self.player1.get_photo()
        
    def get_photo_player2(self):
        return self.player2.get_photo()
        