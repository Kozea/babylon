# all the imports
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
import Match
import Team
import User

# configuration
DATABASE = '/tmp/babylone.db'
DEBUG = True
SECRET_KEY = 'development key'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])
    
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
        if(id_player2 is not None):
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
        if(id_player2 is not None):
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
    for cur_player in request_user.fetchall():
        player = User.User(cur_player[0], cur_player[1], cur_player[2],
        cur_player[3], cur_player[4], cur_player[5])
        users.append(player)
    return render_template('ranking.html', users = users)
    
@app.route('/add_match')
def add_match():
    return "add_match"    
    
@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    error = None
    if request.method == 'POST':
        surname = request.form['surname']
        name = request.form['name']
        nickname = request.form['nickname']
        
        if(surname == "" or name == "" or nickname == ""):
            error = "Some fields are empty !"
        
        else :
            cur = g.db.execute('select id_user from users where nickname = ?',
            (nickname,))
            if( cur.fetchone() ):
                error = "This nickname is already used !"
            else:
                cur = g.db.execute('select max(id_user) from users')
                index = cur.fetchone()[0] + 1
                
                g.db.execute("INSERT INTO users VALUES (?, ?, ?, ?, 1000,'photo0')",
                (index, surname, name, nickname,))
                
                g.db.commit()
                
                error = "Let's play !"
        
    return render_template('add_player.html', error = error)
    
    
if __name__ == '__main__':
    app.run()
    
