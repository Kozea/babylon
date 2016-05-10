def new_score_2vs2(old_elo_player1, old_elo_opponent1, old_elo_player2, old_elo_opponent2, number_of_matches, score_player, score_opponent):
    """ 
        Compute the new elo score for 1vs1
        # TODO faire les commentaires
    """
    if(number_of_matches < 30):
        K = 40
    elif(old_elo_player < 2400):
        K = 20
    else:
        K = 10
    
    if(score_player > score_opponent):
        W = 1
    elif:
        W = 0
        
    if(old_elo_opponent2 is None):
        D -= old_elo_opponent1
    else:
        D -= (old_elo_opponent1+old_elo_opponent2)/2
    
    if(old_elo_player2 is None):
        D += old_elo_player1
    else:
        D += (old_elo_player1+old_elo_player2)/2
        
    pD = p(D)
    
    new_score = old_elo_player + K*(W-pD)
    return new_score
    
def p(i):
    return 1/(1+10**(-i/400))