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
    """Called when app is launched , to connect to the Database."""
    return sqlite3.connect(app.config['DATABASE'])
    
def init_db():
    """Initializes the schema of the database."""
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
    db.commit()
    
@app.before_request
def before_request():
    """Called before each query on the database."""
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    """Called after each query on the database."""
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
        
@app.route('/')
def matchs():
    """Querying for all matchs in the database"""
    matchs = []
    request_match = g.db.execute('select id_match, date, score_e1, \
    score_e2, id_player11, id_player12, id_player21, id_player22 \
    from matchs order by date desc')
    
    for match in request_match.fetchall():

        # Create player1
        id_player11 = match[4]
        request_user = g.db.execute('select id_user, surname, name, \
        nickname, photo from users where id_user = ?', (id_player11,))
        cur_player11 = request_user.fetchone()
        player11 = User.User(cur_player11[0], cur_player11[1], cur_player11[2],
        cur_player11[3], cur_player11[4])
        
        # Create player2 if exists
        id_player12 = match[5]
        if(id_player12 is not None and id_player12 != ''):
            request_user2 = g.db.execute('select id_user, surname, name,\
            nickname, photo from users where id_user = ?',
            (id_player12,))
            cur_player12 = request_user2.fetchone()
            player12 = User.User(cur_player12[0], cur_player12[1],
            cur_player12[2], cur_player12[3], cur_player12[4])
        else:
            player12 = None
        

        # Create player1
        id_player21 = match[6]
        request_user = g.db.execute('select id_user, surname, name, \
        nickname, photo from users where id_user = ?',
        (id_player21,))
        cur_player21 = request_user.fetchone()
        player21 = User.User(cur_player21[0], cur_player21[1], cur_player21[2],
        cur_player21[3], cur_player21[4])
        
        # Create player2 if exists
        id_player22 = match[7]
        if(id_player22 is not None and id_player22 != ''):
            request_user2 = g.db.execute('select id_user, surname, \
            name, nickname, photo from users where id_user = ?',
            (id_player22,))
            cur_player22 = request_user2.fetchone()
            player22 = User.User(cur_player22[0], cur_player22[1],
            cur_player22[2], cur_player22[3], cur_player22[4])
        else:
            player22 = None
            
        # Create the match
        match_to_add = Match.Match(match[0], match[1], match[2], match[3],
        player11, player12, player21, player22)
        matchs.append(match_to_add)
        
    return render_template('match.html', matchs = matchs)
    
@app.route('/ranking')
def ranking():
    """Querying for the ranking"""
    unordered_ranking = compute_ranking().values()
    ordered_ranking = sorted(unordered_ranking, key = lambda user: -user.ranking)
    return render_template('ranking.html', users = ordered_ranking)
    
@app.route('/add_match')
def add_match():
    """Allows user to access the match adding form."""
    users = []
    request_user = g.db.execute('select id_user, surname, name, nickname,\
     photo from users')
    
    # Get all users
    for cur_player in request_user.fetchall():
        player = User.User(cur_player[0], cur_player[1], cur_player[2],
        cur_player[3], cur_player[4])
        users.append(player)
    
    print(users)
    if(len(users) == 0):
        success = "There are no players yet !"
        return render_template('add_match.html',success = success, user = True)
        
    return render_template('add_match.html', users = users)   
    
@app.route('/new_match', methods=['POST'])


def new_match():
    """Creates a new match using values given to the add_match form"""    
    users = []
    request_user = g.db.execute('select id_user, surname, name, nickname,\
     photo from users')
    
    for cur_player in request_user.fetchall():
        player = User.User(cur_player[0], cur_player[1], cur_player[2],
        cur_player[3], cur_player[4],)
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
            
            
        id_player11 = request.form['id_player11']
        id_player12 = request.form['id_player12']
        id_player21 = request.form['id_player21']
        id_player22 = request.form['id_player22']
        
        score_e1 = request.form['score_e1']
        score_e2 = request.form['score_e2']
        
        #Adding New Match
        g.db.execute('insert into matchs (date, score_e1, score_e2,\
                    id_player11, id_player12, id_player21, id_player22) \
                    values (?, ?, ?, ?, ?, ?, ?)',
                    (time.strftime("%d/%m/%Y"), score_e1, score_e2, id_player11, id_player12, id_player21, id_player22 ))
        g.db.commit()
        
        
        #~ # get old elo for 11
        #~ cur = g.db.execute('select ranking from users where id_user =?',
                            #~ (id_player11,))
        #~ old_elo_player11 = cur.fetchone()[0]
        
        #~ cur = g.db.execute('select numberMatchs from users where id_user =?',
                            #~ (id_player11,))
        #~ number11 = cur.fetchone()[0]+1
        #~ g.db.execute('update users set numberMatchs = ? where id_user = ?',
                            #~ (number11, id_player11,))
        #~ g.db.commit()
        
       
        #~ # get old elo for 12
        #~ if(request.form['id_player12']):
            #~ cur = g.db.execute('select ranking from users where id_user =?',
                            #~ (id_player12,))
            #~ old_elo_player12 = cur.fetchone()[0]
            
            #~ cur = g.db.execute('select numberMatchs from users where id_user =?',
                            #~ (id_player12,))
            #~ number12 = cur.fetchone()[0]+1
            #~ g.db.execute('update users set numberMatchs = ? where id_user = ?',
                            #~ (number12, id_player12,))
            #~ g.db.commit()
        #~ else:
            #~ old_elo_player12 = None
            
        #~ # get old elo for 21
        #~ cur = g.db.execute('select ranking from users where id_user =?',
                        #~ (id_player21,))
        #~ old_elo_player21 = cur.fetchone()[0]
        
        #~ cur = g.db.execute('select numberMatchs from users where id_user =?',
                        #~ (id_player21,))
        #~ number21 = cur.fetchone()[0]+1
        #~ g.db.execute('update users set numberMatchs = ? where id_user = ?',
                        #~ (number21, id_player21,))
        #~ g.db.commit()
        
        #~ # get old elo for 22
        #~ if(request.form['id_player22']):
            #~ cur = g.db.execute('select ranking from users where id_user =?',
                        #~ (id_player22,))
            #~ old_elo_player22 = cur.fetchone()[0]
            
            #~ cur = g.db.execute('select numberMatchs from users where id_user =?',
                        #~ (id_player22,))
            #~ number22 = cur.fetchone()[0]+1
            #~ g.db.execute('update users set numberMatchs = ? where id_user = ?',
                        #~ (number22, id_player22,))
            #~ g.db.commit()
                    
        #~ else:
            #~ old_elo_player22 = None
            
        #~ # Modify score for 11
        #~ newelo11 =Elo.new_score(old_elo_player11, old_elo_player21, old_elo_player12, 
        #~ old_elo_player22, number11, score_e1, score_e2)
        
        #~ g.db.execute('update users set ranking = ? where id_user = ?',
                    #~ (newelo11,id_player11,))
        #~ g.db.commit()
    
        #~ # Modify score for 12 if necessary
        #~ if(request.form['id_player12']):
            #~ newelo12 = Elo.new_score(old_elo_player12, old_elo_player21, 
            #~ old_elo_player11, old_elo_player22, number12, score_e1, score_e2)
            
            #~ g.db.execute('update users set ranking = ? where id_user = ?',
                        #~ (newelo12,id_player12,))
                        
            #~ g.db.commit()
            
        #~ # Modify score for 21
        #~ newelo21 = Elo.new_score(old_elo_player21, old_elo_player11, 
                    #~ old_elo_player22, old_elo_player12, number21, 
                    #~ score_e2, score_e1)
        
        #~ g.db.execute('update users set ranking = ? where id_user = ?',
                    #~ (newelo21,id_player21,))
        #~ g.db.commit()
        
        #~ # Modify score for 22 if necessary
        #~ if(request.form['id_player22']):
            #~ newelo22 = Elo.new_score(old_elo_player22, old_elo_player11, 
            #~ old_elo_player22, old_elo_player12, number22, score_e2, score_e1)
            
            #~ g.db.execute('update users set ranking = ? where id_user = ?',
                        #~ (newelo22,id_player22,))
            #~ g.db.commit()
                
        success = "Match was successfully added "
               
    return render_template('add_match.html', success = success, 
                            error = error, users = users)
       
    
@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
"""Creates a new user using values given in the add_player form"""
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
                g.db.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                (index, surname, name, nickname, filename,))
                
                g.db.commit()
                
                error = "Let's play !"
        
    return render_template('add_player.html', error = error)
 
                               
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
           
####### HELPER #########
def number_of_match(id_player):
    """
        Returns the number of matches played by a player
        
        :param id_player: ID of the player
        :return: Number of matches played by the player
    """
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

    
def compute_ranking():
    """Calculates score for each player, using matches played by the user."""
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
    
