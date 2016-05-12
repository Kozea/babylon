# all the imports
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, send_from_directory
from werkzeug import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os
import time
from PIL import Image
from resizeimage import resizeimage


# DO NOT DELETE OR MOVE THIS LINE
from Model import User, Match
from database import *
   
@app.route('/')
def matchs():
    """Querying for all matchs in the database"""
    matchs = Match.query.all()
    return render_template('match.html', matchs = matchs)


@app.route('/ranking')
def ranking():
    """Querying for the ranking"""
    unordered_ranking = compute_ranking()
    ordered_ranking = sorted(unordered_ranking, key = lambda user: -user.ranking)
    return render_template('ranking.html', users = ordered_ranking)


@app.route('/add_match')
def add_match():
    """Allows user to access the match adding form."""

    users = User.query.all()
      
    if(len(users) == 0):
        success = "There are no players yet !"
        return render_template('add_match.html',success = success, user = True)

    return render_template('add_match.html', users = users)   


@app.route('/new_match', methods=['POST'])
def new_match():
    """Creates a new match using values given to the add_match form"""
        
    users = User.query.all()

    error = None
    success = None

    # Check if some players are missing
    if not request.form['id_player11']:
        error = 'Add a player 1 to team 1'
    elif not request.form['id_player21']:
        error = 'Add a player 1 to team 2'

    # Check if some users appear twice
    elif ((request.form['id_player11'] == request.form['id_player12']) or 
          (request.form['id_player11'] == request.form['id_player21']) or
          (request.form['id_player11'] == request.form['id_player22']) or
          (request.form['id_player12'] == request.form['id_player21']) or
          (request.form['id_player12'] == request.form['id_player22'] and
          (request.form['id_player12'])) or
          (request.form['id_player21'] == request.form['id_player22'])):
        error = 'Please select different users'

    elif not request.form['score_e1']:
        error = 'Add a score for Team 1'

    elif not request.form['score_e2']:
        error = 'Add a score for Team 2'

    else:
        id_player11 = request.form['id_player11']
        id_player12 = request.form['id_player12']
        id_player21 = request.form['id_player21']
        id_player22 = request.form['id_player22']

        score_e1 = request.form['score_e1']
        score_e2 = request.form['score_e2']

        # Adding New Match
        #~ g.db.execute('insert into matchs (date, score_e1, score_e2,\
                    #~ id_player11, id_player12, id_player21, id_player22) \
                    #~ values (?, ?, ?, ?, ?, ?, ?)',
                    #~ (time.strftime("%d/%m/%Y"), score_e1, score_e2,
                     #~ id_player11, id_player12, id_player21,
                     #~ id_player22))
                     
        match = Match((time.strftime("%d/%m/%Y"), score_e1, score_e2,
                      id_player11, id_player12, id_player21,
                      id_player22))

        db.session.add(match)
        db.session.commit()

        success = "Match was successfully added "

    return render_template('add_match.html', success=success,
                           error=error, users=users)


@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    """Creates a new user using values given in the add_player form"""

    error = None
    if request.method == 'POST':
        # Get user infos
        surname = request.form['surname']
        name = request.form['name']
        nickname = request.form['nickname']

        filename =""
        # Get user photo and work on it
        photo = request.files['photo']
        if photo and allowed_file(photo.filename):
            filename = app.config['UPLOAD_FOLDER']+"/"+nickname+get_extension_file(photo.filename)
            photo.save(filename)
            with open(filename, 'r+b') as f:
                with Image.open(f) as image:
                    cover = resizeimage.resize_contain(image, [200, 100])
                    cover.save(filename, image.format)

        # If some field are empty
        if(surname == "" or name == "" or nickname == ""):
            error = "Some fields are empty !"

        else:
            # Check if user already exists
            cur = User.query.filter_by(nickname = request.form['nickname']).first()
            if(cur):
                error = "This nickname is already used !"
            else:
              
                # Add the new user to the database
                
                new_user = User(surname, name, nickname,filename)
                #~ g.db.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                             #~ (index, surname, name, nickname,
                              #~ filename,))

                db.session.add(new_user)
                db.session.commit()

                error = "Let's play !"

    return render_template('add_player.html', error=error)


def get_extension_file(filename):
    """
        Return the extension of a file

        :param filename: The full name of the file
        :return: The extension of the file
    """

    index = filename.rfind('.')
    return filename[index:]


def allowed_file(filename):
    """ Test to know if a file has a correct extension.  """

    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/coucou')
def coucou():
    toRet = ""
    matchs = Match.query.all()
    
    for match in matchs:
        match.player11.set_ranking(1000)
        match.player12.set_ranking(1000)
        match.player21.set_ranking(1000)
        match.player22.set_ranking(1000)
        match.player11.set_number_of_matchs()
        match.player12.set_number_of_matchs()
        match.player21.set_number_of_matchs()
        match.player22.set_number_of_matchs()
        
    for match in matchs:
        elo(match.player11, match.player12,match.player21,match.player22,
            match.score_e1, match.score_e2)
            
    users = User.query.all()
    for user in users:
        toRet += str(user.ranking)
        toRet+='<br>'
    return toRet
# HELPER #

def compute_ranking():
    matchs = Match.query.all()
    
    for match in matchs:
        match.player11.set_ranking(1000)
        match.player12.set_ranking(1000)
        match.player21.set_ranking(1000)
        match.player22.set_ranking(1000)
        match.player11.set_number_of_matchs()
        match.player12.set_number_of_matchs()
        match.player21.set_number_of_matchs()
        match.player22.set_number_of_matchs()
        
    for match in matchs:
        elo(match.player11, match.player12,match.player21,match.player22,
            match.score_e1, match.score_e2)
            
    users = User.query.all()

    return users

def elo(me, my_friend, my_ennemy1, my_ennemy2, my_score, opponent_score):
    # Create fictive player1
    if(my_friend is None):
        elo1 =  me.ranking
        number_match1 = me.number_of_match
    else:
        elo1 = (me.ranking+my_friend.ranking)/2
        number_match1 = (me.number_of_match+my_friend.number_of_match)/2
    
    # Create fictive player2
    if(my_ennemy2 is None):
        elo2 =  my_ennemy1.ranking
        number_match2 = my_ennemy1.number_of_match
    else:
        elo2 = (my_ennemy1.ranking+my_ennemy2.ranking)/2
        number_match2 = (my_ennemy1.number_of_match+my_ennemy2.number_of_match)/2
    
    
    # Score for player1
    We1 = p(my_score-opponent_score)
    K = chooseK(number_match1, elo1)
    G = chooseG(my_score, opponent_score)
    W = chooseW(my_score, opponent_score)
    score_p1 = K*G*(W-We1)
    
    # Score for player2
    We2 = 1 - We1
    K = chooseK(number_match2, elo2)
    G = chooseG(opponent_score, my_score)
    W = chooseW(opponent_score, my_score)
    score_p2 = K*G*(W-We2)
    
    # Get points to real users
    if(my_friend is None):
        me.ranking += int(round(score_p2,0))
        me.number_of_match += 1
    else:
        sum_ranking = me.ranking+my_friend.ranking
        # update my score
        me.ranking += int(round((me.ranking/sum_ranking)*score_p1,0))
        me.number_of_match += 1  
        # update my friend score
        my_friend.ranking += int(round((my_friend.ranking/sum_ranking)*score_p1,0))
        my_friend.number_of_match += 1  
        
    if(my_ennemy2 is None):
        my_ennemy1.ranking += int(round((score_p1),0))
        my_ennemy1.number_of_match += 1
    else:
        sum_ranking = my_ennemy1.ranking+my_ennemy2.ranking
        # update my score
        my_ennemy1.ranking += int(round((my_ennemy1.ranking/sum_ranking)*score_p2,0))
        my_ennemy1.number_of_match += 1  
        # update my friend score
        my_ennemy2.ranking += int(round((my_ennemy2.ranking/sum_ranking)*score_p2,0))
        my_ennemy2.number_of_match += 1  
    
def chooseK(number_of_match, elo):
    if(number_of_match < 40):
        return 40
    elif(elo<2400):
        return 20
    else:
        return 10
        
def chooseG(score_e1, score_e2):
    diff = abs(score_e1 - score_e2)
    if(diff <2):
        G = 1
    elif(diff == 2):
        G = 1+1/2
    elif(diff == 3):
        G = 1+3/4
    else:
        G = 1+3/4+(diff-3)/8
    return G
    
def chooseW(score_e1, score_e2):
    return 1 if score_e1 > score_e2 else 0
    
def p(i):
    return 1/(1+10**(-i/400))
    
if __name__ == '__main__':
    app.run()
