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
        return self.player1.get_full_name()
        
    def get_team_name(self):
        return self.name
    