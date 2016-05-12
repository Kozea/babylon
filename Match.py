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
