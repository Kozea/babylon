from statistics import stdev
import sys
import random
import threading
import math

class Joueur:
    
    def __init__(self,name,rank):
        self.rank = rank
        self.name = name
        
def generate_tournament(participants):
    number_of_participants = len(participants)
    if(number_of_participants%2 != 0):
        raise Exception("You must be a power of 2 !")
                
    #get the list of all players
    players = participants
    
    # ordered the list of all players
    players = sorted(players, key=lambda player: player.rank)  
    
    # create the team
    teams = [(players[i], players[len(players)-1-i]) 
                for i in range(math.floor(len(players)/2))]    
        
    # ordered the team
    teams = sorted(teams, key=lambda team: (team[0].rank+team[1].rank)/2)
    
    index = 1
    for team in teams:
        print(index, (team[0].rank+team[1].rank)/2)
        index += 1

    tournament_head = []
    tournament_queue = []
    first = True
    # create the tournament to make distance between contenders
    for i in range(math.floor(len(teams)/2)):
        if(first):
            tournament_head.append(((teams[i]),teams[len(teams)-1-i]))
        else:
            tournament_queue.insert(0,((teams[i]),teams[len(teams)-1-i]))
        first = not first
        
    tournament = tournament_head + tournament_queue
    
    print("TOURNAMENT")
    for (team1, team2) in tournament:
        print(team1[0].name, team1[0].rank)
        print(team1[1].name, team1[1].rank)
        print((team1[0].rank+team1[1].rank)/2)        
        print(team2[0].name, team2[0].rank)
        print(team2[1].name, team2[1].rank)
        print((team2[0].rank+team2[1].rank)/2)        
        print()
        
def all_pairs(lst):
    if len(lst) < 2:
        yield lst
        return
    a = lst[0]
    for i in range(1,len(lst)):
        pair = (a,lst[i])
        for rest in all_pairs(lst[1:i]+lst[i+1:]):
            yield [pair] + rest
    
def build_avg_temp(pairs, participants):
    s = []
    for pair in pairs:
        temp_avg = (participants[pair[0]].rank+participants[pair[1]].rank)/2
        s.append(temp_avg)
    #~ print("AVG",s)
    return s
    
participants = []
for i in range(16):
    participants.append(Joueur("Paul"+str(i),random.randint(0,500)))

generate_tournament(participants)
