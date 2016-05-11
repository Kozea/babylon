# all the imports
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
import Match
import time

# configuration
DATABASE = '/tmp/babylone.db'
DEBUG = True
SECRET_KEY = 'development key'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])
    
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
    db.commit()
    
@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
        
@app.route('/')
def matchs():
    matchs = []
    return render_template('match.html', matchs=matchs)
    
@app.route('/ranking')
def ranking():
    return "Classement"
    
@app.route('/add_match')
def add_match():
    return render_template('add_match.html')   
    
@app.route('/new_match', methods=['POST'])
def new_match():
    
    error = None
    
    if not request.form['id_player11'] :
        error = 'Add a player 1 to team 1'
    elif not request.form['id_player21']:
        error = 'Add a player 1 to team 2'
    elif not request.form['score_e1'] :
        error = 'Add a score for Team 1'
    elif not request.form['score_e2'] :
        error = 'Add a score for Team 2'
        
    else:  
        # Searching Team 1 in database
        request_team1 = g.db.execute('select * from teams where((id_player1=? and id_player2=?) or (id_player1=? and id_player2=?))',
                                            (request.form['id_player11'], request.form['id_player12'], request.form['id_player12'], request.form['id_player11']))                       
        
        # Creating team if doesn't exist
        result = request_team1.fetchone()
        if (not result):
            temp = g.db.execute('select max(id_team) from teams')
            index1 = temp.fetchone()[0]+1
            g.db.execute('insert into teams values (?,?,?,null)', (index1, request.form['id_player11'], request.form['id_player12']))
            id_t1 = index1
            
        else:
            id_t1 = result[0]
        
            
        # Searching Team 2 in database
        request_team2 = g.db.execute('select * from teams where((id_player1=? and id_player2=?) or (id_player1=? and id_player2=?))',
                                            (request.form['id_player21'], request.form['id_player22'], request.form['id_player22'], request.form['id_player21']))                       
        
        # Creating team if doesn't exist
        result = request_team2.fetchone()
        if (not result):
            temp = g.db.execute('select max(id_team) from teams')
            index2 = temp.fetchone()[0]+1
            g.db.execute('insert into teams values (?,?,?,null)', (index2, request.form['id_player21'], request.form['id_player22']))
            id_t2 = index2
            
        else:
            id_t2 = result[0]
            
            
        #Adding New Match
        g.db.execute('insert into matchs (date, id_team1, id_team2, score_e1, score_e2) values (?, ?, ?, ?, ?)',
                     (time.strftime("%d/%m/%Y"), id_t1, id_t2, request.form['score_e1'], request.form['score_e2']))
        g.db.commit()
        
        flash('Le match a été ajouté avec succès')
        
        return redirect(url_for('add_match'))
        
    return render_template('add_match.html', error=error)
    
@app.route('/add_player')
def add_player():
    return "ajout_joueur"
    
    

    
if __name__ == '__main__':
    app.run()
    
