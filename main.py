# all the imports
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, send_from_directory
from werkzeug import secure_filename
import os
import Elo
import Match
import User
import time
from PIL import Image
from resizeimage import resizeimage

# configuration
DATABASE = '/tmp/babylone.db'
DEBUG = True
SECRET_KEY = 'development key'
UPLOAD_FOLDER = './static/image_flask'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])
    
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
    db.commit()
    
@app.before_request
def before_request():
    """
        Called before each query on the database.
    """
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    """
        Called after each query on the database.
    """
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
        
@app.route('/')
def matchs():
    """
        Querying for all matchs in the database
    """
    matchs = []
    request_match = g.db.execute('select id_match, date, score_e1, \
    score_e2, id_team1, id_team2 from matchs order by date desc')
    for match in request_match.fetchall():
        # Create the team1
        id_team1 = match[4]
        request_team = g.db.execute('select id_team, id_player1, \
        id_player2, name from teams where id_team =?', (id_team1,))
        team1 = request_team.fetchone()

        # Create player1
        id_player1 = team1[1]
        request_user = g.db.execute('select id_user, surname, name, \
        nickname, ranking, photo from users where id_user = ?', (id_player1,))
        cur_player1 = request_user.fetchone()
        player1 = User.User(cur_player1[0], cur_player1[1], cur_player1[2],
        cur_player1[3], cur_player1[4], cur_player1[5])
        
        # Create player2 if exists
        id_player2 = team1[2]
        if(id_player2 is not None and id_player2 != ''):
            request_user2 = g.db.execute('select id_user, surname, name,\
            nickname, ranking, photo from users where id_user = ?',
            (id_player2,))
            cur_player2 = request_user2.fetchone()
            player2 = User.User(cur_player2[0], cur_player2[1],
            cur_player2[2], cur_player2[3], cur_player2[4], cur_player2[5])
        else:
            player2 = None
        
        cur_team1 = Team.Team(id_team1, player1, player2, team1[3])
                    
        # Create the team2
        id_team2 = match[5]
        request_team = g.db.execute('select id_team, id_player1, \
        id_player2, name from teams where id_team =?', (id_team2,))
        team2 = request_team.fetchone()

        # Create player1
        id_player1 = team2[1]
        request_user = g.db.execute('select id_user, surname, name, \
        nickname, ranking, photo from users where id_user = ?',
        (id_player1,))
        cur_player1 = request_user.fetchone()
        player1 = User.User(cur_player1[0], cur_player1[1], cur_player1[2],
        cur_player1[3], cur_player1[4], cur_player1[5])
        
        # Create player2 if exists
        id_player2 = team2[2]
        if(id_player2 is not None and id_player2 != ''):
            request_user2 = g.db.execute('select id_user, surname, \
            name, nickname, ranking, photo from users where id_user = ?',
            (id_player2,))
            cur_player2 = request_user2.fetchone()
            player2 = User.User(cur_player2[0], cur_player2[1],
            cur_player2[2], cur_player2[3], cur_player2[4], cur_player2[5])
        else:
            player2 = None
            
        cur_team2 = Team.Team(id_team2, player1, player2, team2[3])

        # Create the match
        match_to_add = Match.Match(match[0], match[1], match[2], match[3],
        cur_team1, cur_team2)
        matchs.append(match_to_add)
        
    return render_template('match.html', matchs = matchs)
    
@app.route('/ranking')
def ranking():
    """
        Querying for the ranking
    """
    users = []
    request_user = g.db.execute('select id_user, surname, name, nickname,\
    ranking, photo from users order by ranking desc')
    rank = 1
    # Get all users and rank
    for cur_player in request_user.fetchall():
        player = User.User(cur_player[0], cur_player[1], cur_player[2],
        cur_player[3], cur_player[4], cur_player[5])
        users.append((rank, player))
        rank += 1
    return render_template('ranking.html', users = users)
    
@app.route('/add_match')
def add_match():
    users = []
    request_user = g.db.execute('select id_user, surname, name, nickname,\
    ranking, photo from users')
    
    # Get all users
    for cur_player in request_user.fetchall():
        player = User.User(cur_player[0], cur_player[1], cur_player[2],
        cur_player[3], cur_player[4], cur_player[5])
        users.append(player)
    
    print(users)
    if(len(users) == 0):
        success = "There are no players yet !"
        return render_template('add_match.html',success = success, user = True)
        
    return render_template('add_match.html', users = users)   
    
@app.route('/new_match', methods=['POST'])
def new_match():
    
    users = []
    request_user = g.db.execute('select id_user, surname, name, nickname,\
    ranking, photo from users')
    
    for cur_player in request_user.fetchall():
        player = User.User(cur_player[0], cur_player[1], cur_player[2],
        cur_player[3], cur_player[4], cur_player[5])
        users.append(player)
        
    error = None
    success = None
    
    
    
    # Check if some players are missing
    if not request.form['id_player11']:
        error = 'Add a player 1 to team 1'
    elif not request.form['id_player21']:
        error = 'Add a player 1 to team 2'
        
    # Check if some users appear twice
    elif ((request.form['id_player11'] == request.form['id_player12'])
        or (request.form['id_player11'] == request.form['id_player21'])
        or (request.form['id_player11'] == request.form['id_player22'])
        or (request.form['id_player12'] == request.form['id_player21'])
        or (
        request.form['id_player12'] == request.form['id_player22']
        and request.form['id_player12']
        )
        
        or (request.form['id_player21'] == request.form['id_player22'])):
        
        error = 'Please select different users'
    
    elif not request.form['score_e1'] :
        error = 'Add a score for Team 1'
    elif not request.form['score_e2'] :
        error = 'Add a score for Team 2'
    
        
    else:  
        # Searching Team 1 in database
        request_team1 = g.db.execute('select * from teams where\
                                    ((id_player1=? and id_player2=?) \
                                    or (id_player1=? and id_player2=?))',
                                    (request.form['id_player11'], 
                                    request.form['id_player12'], 
                                    request.form['id_player12'], 
                                    request.form['id_player11']))                       
        
        # Creating team if doesn't exist
        result = request_team1.fetchone()
        if (not result):
            temp = g.db.execute('select max(id_team) from teams')
            
            res = temp.fetchone()
            if(res):
                if(res[0] is None):
                    index1 = 0
                else:
                    index1 = res[0] + 1
                        
            g.db.execute('insert into teams values (?,?,?,null)', 
                        (index1, request.form['id_player11'], 
                        request.form['id_player12']))
            id_t1 = index1
            
        else:
            id_t1 = result[0]
        
            
        # Searching Team 2 in database
        request_team2 = g.db.execute('select * from teams where\
                                    ((id_player1=? and id_player2=?) or \
                                    (id_player1=? and id_player2=?))',
                                    (request.form['id_player21'], 
                                    request.form['id_player22'], 
                                    request.form['id_player22'], 
                                    request.form['id_player21']))                       
        
        # Creating team if doesn't exist
        result = request_team2.fetchone()
        if (not result):
            temp = g.db.execute('select max(id_team) from teams')
            
            res = temp.fetchone()
            if(res):
                if(res[0] is None):
                    index2 = 0
                else:
                    index2 = res[0] + 1
            g.db.execute('insert into teams values (?,?,?,null)', 
                        (index2, request.form['id_player21'], 
                        request.form['id_player22']))
            id_t2 = index2
            
        else:
            id_t2 = result[0]
            
            
        #Adding New Match
        g.db.execute('insert into matchs (date, id_team1, id_team2, \
                    score_e1, score_e2) values (?, ?, ?, ?, ?)',
                    (time.strftime("%d/%m/%Y"), id_t1, id_t2, 
                    request.form['score_e1'], request.form['score_e2']))
        g.db.commit()
        
        # update rank
        id_player11 = request.form['id_player11']
        id_player12 = request.form['id_player12']
        id_player21 = request.form['id_player21']
        id_player22 = request.form['id_player22']
        
        score_e1 = request.form['score_e1']
        score_e2 = request.form['score_e2']
        
        # get old elo for 11
        cur = g.db.execute('select ranking from users where id_user =?',
                            (id_player11,))
        old_elo_player11 = cur.fetchone()[0]
        
        cur = g.db.execute('select numberMatchs from users where id_user =?',
                            (id_player11,))
        number11 = cur.fetchone()[0]+1
        g.db.execute('update users set numberMatchs = ? where id_user = ?',
                            (number11, id_player11,))
        g.db.commit()
        
       
        # get old elo for 12
        if(request.form['id_player12']):
            cur = g.db.execute('select ranking from users where id_user =?',
                            (id_player12,))
            old_elo_player12 = cur.fetchone()[0]
            
            cur = g.db.execute('select numberMatchs from users where id_user =?',
                            (id_player12,))
            number12 = cur.fetchone()[0]+1
            g.db.execute('update users set numberMatchs = ? where id_user = ?',
                            (number12, id_player12,))
            g.db.commit()
        else:
            old_elo_player12 = None
            
        # get old elo for 21
        cur = g.db.execute('select ranking from users where id_user =?',
                        (id_player21,))
        old_elo_player21 = cur.fetchone()[0]
        
        cur = g.db.execute('select numberMatchs from users where id_user =?',
                        (id_player21,))
        number21 = cur.fetchone()[0]+1
        g.db.execute('update users set numberMatchs = ? where id_user = ?',
                        (number21, id_player21,))
        g.db.commit()
        
        # get old elo for 22
        if(request.form['id_player22']):
            cur = g.db.execute('select ranking from users where id_user =?',
                        (id_player22,))
            old_elo_player22 = cur.fetchone()[0]
            
            cur = g.db.execute('select numberMatchs from users where id_user =?',
                        (id_player22,))
            number22 = cur.fetchone()[0]+1
            g.db.execute('update users set numberMatchs = ? where id_user = ?',
                        (number22, id_player22,))
            g.db.commit()
                    
        else:
            old_elo_player22 = None
            
        # Modify score for 11
        newelo11 =Elo.new_score(old_elo_player11, old_elo_player21, old_elo_player12, 
        old_elo_player22, number11, score_e1, score_e2)
        
        g.db.execute('update users set ranking = ? where id_user = ?',
                    (newelo11,id_player11,))
        g.db.commit()
    
        # Modify score for 12 if necessary
        if(request.form['id_player12']):
            newelo12 = Elo.new_score(old_elo_player12, old_elo_player21, 
            old_elo_player11, old_elo_player22, number12, score_e1, score_e2)
            
            g.db.execute('update users set ranking = ? where id_user = ?',
                        (newelo12,id_player12,))
                        
            g.db.commit()
            
        # Modify score for 21
        newelo21 = Elo.new_score(old_elo_player21, old_elo_player11, 
                    old_elo_player22, old_elo_player12, number21, 
                    score_e2, score_e1)
        
        g.db.execute('update users set ranking = ? where id_user = ?',
                    (newelo21,id_player21,))
        g.db.commit()
        
        # Modify score for 22 if necessary
        if(request.form['id_player22']):
            newelo22 = Elo.new_score(old_elo_player22, old_elo_player11, 
            old_elo_player22, old_elo_player12, number22, score_e2, score_e1)
            
            g.db.execute('update users set ranking = ? where id_user = ?',
                        (newelo22,id_player22,))
            g.db.commit()
                
        success = "Match was successfully added "
               
    return render_template('add_match.html', success = success, 
                            error = error, users = users)
       
    
@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    error = None
    if request.method == 'POST':
        # Get user infos
        surname = request.form['surname']
        name = request.form['name']
        nickname = request.form['nickname']
        
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
        
        else :
            # Check if user already exists
            cur = g.db.execute('select id_user from users where nickname = ?',
            (nickname,))
            if( cur.fetchone() ):
                error = "This nickname is already used !"
            else:
                # Find the new index
                cur = g.db.execute('select max(id_user) from users')
                res = cur.fetchone()
                if(res):
                    if(res[0] is None):
                        index = 0
                    else:
                        index = res[0] + 1
                else:
                    index = 0
                
                # Add the new user to the database
                g.db.execute("INSERT INTO users VALUES (?, ?, ?, ?, 1000,?, 0)",
                (index, surname, name, nickname, filename,))
                
                g.db.commit()
                
                error = "Let's play !"
        
    return render_template('add_player.html', error = error)
 
                               
def get_extension_file(filename):
    """
        Return the extension of the file
    """
    index = filename.rfind('.')
    return filename[index:]
    
    
def allowed_file(filename):
    """
        Test to know if a file has a correct extension.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
           
####### HELPER #########
def number_of_match(id_player):
    query = "select count(id_match)\
            from matchs\
            where id_player11 = num\
            or id_player12 = num\
            or id_player21 = num\
            or id_player22 = num"
            
    query = query.replace("num",str(id_player))
    cursor = g.db.execute(query)
    results = cursor.fetchone()
    if(results):
        number = results[0]
    else:
        number = 0
    return number

@app.route('/coucou')
def coucou():
    users = compute_ranking()
    toRet = ""
    for k,v in users.items():
        toRet += v.get_full_name()+" "+str(v.ranking)+"<br>"
    return toRet
    
def compute_ranking():
    # Get all users
    users = {}
    request_user = g.db.execute('select id_user, surname, name, nickname,\
                                photo from users')
    for cur_user in request_user.fetchall():
        player = User.User(cur_user[0], cur_user[1], cur_user[2],
        cur_user[3], cur_user[4])
        users[cur_user[0]] = player
    
    # Get all matchs
    matchs = []
    request_match = g.db.execute('select id_match, date, score_e1, score_e2,\
                                 id_player11, id_player12, id_player21, \
                                 id_player22 from matchs')
    for cur_match in request_match.fetchall():
        id_player11 = users[cur_match[4]]
        id_player12 = users[cur_match[5]] if cur_match[5] in users.keys() else None
        id_player21 = users[cur_match[6]]
        id_player22 = users[cur_match[7]] if cur_match[7] in users.keys() else None
        match = Match.Match(cur_match[0], cur_match[1], cur_match[2],
                            cur_match[3], id_player11, id_player12,
                            id_player21, id_player22)
        matchs.append(match)
        
    # For each match
    for match in matchs:
        # Get all players and actuals scores
        player11 = match.player11
        old_elo11 = player11.ranking
        
        player12 = match.player12
        old_elo12 = player12.ranking if player12 is not None else None
        
        player21 = match.player21
        old_elo21 = player21.ranking 
        
        player22 = match.player22
        old_elo22 = player22.ranking if player22 is not None else None
                
        # For player11
        new_score11 = Elo.new_score(old_elo11, old_elo21, 
                                old_elo12, old_elo22, 
                                player11.number_of_match, match.score_e1, 
                                match.score_e2)
        match.player11.ranking = new_score11
        match.player11.number_of_match += 1
        
        # For player12 if necessary
        if(player12 is not None):
            new_score12 = Elo.new_score(old_elo12, old_elo21, 
                                    old_elo11, old_elo22, 
                                    player12.number_of_match, match.score_e1, 
                                    match.score_e2)
            match.player12.ranking = new_score12
            match.player12.number_of_match += 1
        
        # For player21
        new_score21 = Elo.new_score(old_elo21, old_elo11, 
                                old_elo22, old_elo12, 
                                player21.number_of_match, match.score_e2, 
                                match.score_e1)
        
        match.player21.ranking = new_score21
        match.player21.number_of_match += 1
        
        # For player 22 if necessary
        if(player22 is not None):
            new_score22 = Elo.new_score(old_elo22, old_elo11, 
                                    old_elo21, old_elo12, 
                                    player22.number_of_match, match.score_e2, 
                                    match.score_e1)
            match.player22.ranking = new_score22
            match.player22.number_of_match += 1
                
    return users
            
if __name__ == '__main__':
    app.run()
    
