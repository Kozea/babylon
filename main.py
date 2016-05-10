# all the imports
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
import Match

# configuration
DATABASE = '/tmp/babylonel.db'
DEBUG = True
SECRET_KEY = 'development key'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])
    
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
    return "add_match"    
    
@app.route('/add_player')
def add_player():
    return "ajout_joueur"
    
    
if __name__ == '__main__':
    app.run()
    
