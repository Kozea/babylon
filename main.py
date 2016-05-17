# all the imports
from flask import request, render_template, redirect, url_for, Flask
from PIL import Image
from resizeimage import resizeimage
from datetime import datetime
import pygal
import math
from itertools import groupby
from copy import deepcopy
from collections import OrderedDict
from flask_sqlalchemy import SQLAlchemy


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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/babylone.db'
db = SQLAlchemy(app)


class Match(db.Model):
    """This class represents a match in database."""
    id_match = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    score_e1 = db.Column(db.Integer)
    score_e2 = db.Column(db.Integer)
    player11_id = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    player11 = db.relationship('User', foreign_keys=[player11_id])
    player12_id = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    player12 = db.relationship('User', foreign_keys=[player12_id])
    player21_id = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    player21 = db.relationship('User', foreign_keys=[player21_id])
    player22_id = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    player22 = db.relationship('User', foreign_keys=[player22_id])

    def __init__(self, date, score_e1, score_e2, player11,
                 player12, player21, player22):

        self.date = date
        self.score_e1 = score_e1
        self.score_e2 = score_e2
        self.player11 = player11
        self.player12 = player12
        self.player21 = player21
        self.player22 = player22


class User(db.Model):
    """ This class represent a user in data with some others attributes."""
    id_user = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(100))
    name = db.Column(db.String(100))
    nickname = db.Column(db.String(100), unique=True)
    photo = db.Column(db.String(200))

    def __init__(self, surname, name, nickname, photo):
        self.surname = surname
        self.name = name
        self.nickname = nickname
        self.photo = photo
        self.ranking = -1
        self.number_of_match = 0
        self.nb_victories = 0
        self.nb_defeats = 0
        self.ratio_gauge = None

    def get_full_name(self):
        """ Return the full name of a user"""
        return self.surname+" "+self.name

    def set_ranking(self, ranking):
        """ Set the ranking of a user"""
        self.ranking = ranking

    def set_number_of_matchs(self):
        """ Init the number of match."""
        self.number_of_match = 0

player_tournament = 2


@app.route('/')
def matchs():
    """Querying for all matchs in the database"""
    matchs = Match.query.order_by(-Match.id_match).all()
    return render_template('match.html', matchs=matchs)


@app.route('/ranking')
def ranking():
    """
        Querying for the ranking and reaching informations for
        the different chart.
    """
    unordered_ranking = compute_ranking()

    for user in unordered_ranking:
        victories_as_team1 = (
            db.session.query(Match.id_match)
            .filter((Match.player11 == user) | (Match.player12 == user))
            .filter(Match.score_e1 > Match.score_e2)
            .count())
        victories_as_team2 = (
            db.session.query(Match.id_match)
            .filter((Match.player21 == user) | (Match.player22 == user))
            .filter(Match.score_e1 < Match.score_e2)
            .count())

        user.nb_victories = victories_as_team1 + victories_as_team2
        user.nb_defeats = user.number_of_match - user.nb_victories

        if user.number_of_match != 0:
            gauge = pygal.SolidGauge(inner_radius=0.70, show_legend=False)
            gauge.value_formatter = lambda x: '{:.10g}%'.format(x)
            gauge.add(
                'Ratio', [{
                    'value': (user.nb_victories/user.number_of_match)*100,
                    'max_value': 100}])
            user.ratio_gauge = gauge

    ordered_ranking = sorted(
        unordered_ranking, key=lambda user: -user.ranking)
    return render_template('ranking.html', users=ordered_ranking)


@app.route('/tournament', methods=['GET', 'POST'])
def tournament():
    """
        Called when trying to create a tournament.
    """
    users = compute_ranking()
    if request.method == 'POST':
        players = []
        ids_player = request.form.getlist('selectionField')
        for id_player in ids_player:
            players.append(users[int(id_player)])
        tournament = generate_tournament(players)

        return render_template(
            'tournament.html', users=users, tournament=tournament)

    return render_template(
        'tournament.html', users=users)


@app.route('/ranking_graph')
def ranking_graph():
    """
        Draw the ranking chart with a monthly evolution.
    """
    now = datetime.now()
    if now.month-5 != 0:
        date = now.replace(month=now.month-5)
    else:
        date = now.replace(month=12).replace(year=now.year-1)
    date_score = get_ranking_at_timet(date)
    date_score = OrderedDict(sorted(date_score.items(), key=lambda t: t[0]))
    title = 'Monthly Ranking Evolution'
    line_chart = pygal.Line(title=title)
    line_chart.x_labels = [str(date)[0:7] for date in date_score.keys()]

    users_base = User.query.all()

    for user_base in users_base:
        user_array = []
        for date, users in date_score.items():
            for user in users:
                if user.id_user == user_base.id_user:
                    user_array.append(user.ranking)
        line_chart.add(user_base.nickname, user_array)

    return render_template('ranking_graph.html', line_chart=line_chart)


@app.route('/add_match')
def add_match():
    """Allows user to access the match adding form."""

    users = User.query.all()

    if len(users) == 0:
        success = "There are no players yet !"
        return render_template('add_match.html', success=success,
                               user=True)

    return render_template('add_match.html', users=users)


@app.route('/new_match', methods=['POST'])
def new_match():
    """Creates a new match using values given to the add_match form"""

    users = User.query.all()

    error = None
    success = None

    id_player11 = request.form['id_player11']
    id_player12 = request.form['id_player12']
    id_player21 = request.form['id_player21']
    id_player22 = request.form['id_player22']

    score_e1 = request.form['score_e1']
    score_e2 = request.form['score_e2']

    # Check if some players are missing
    if not id_player11:
        error = 'Add a player 1 to team 1'

    elif not id_player21:
        error = 'Add a player 1 to team 2'

    # Check if some users appear twice
    elif ((id_player11 == id_player12) or
          (id_player11 == id_player21) or
          (id_player11 == id_player22) or
          (id_player12 == id_player21) or
          (id_player12 == id_player22 and (id_player12)) or
          (id_player21 == id_player22)):
        error = 'Please select different users'

    elif not score_e1:
        error = 'Add a score for Team 1'

    elif not score_e2:
        error = 'Add a score for Team 2'

    elif not score_e1.isdigit() or not score_e2.isdigit():
        error = 'Please give integer values for score !'

    else:

        player11 = User.query.filter_by(id_user=id_player11).first()
        player12 = User.query.filter_by(id_user=id_player12).first()
        player21 = User.query.filter_by(id_user=id_player21).first()
        player22 = User.query.filter_by(id_user=id_player22).first()

        match = Match(datetime.now(), score_e1, score_e2,
                      player11, player12, player21, player22)

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

        filename = ""
        # Get user photo and work on it
        photo = request.files['photo']
        if photo and allowed_file(photo.filename):
            nickname = nickname.replace(" ", "")
            nickname = nickname.replace("/", "")
            nickname = nickname.replace("\\", "")
            filename = (
                app.config['UPLOAD_FOLDER'] + "/" +
                nickname + get_extension_file(photo.filename))
            photo.save(filename)
            with open(filename, 'r+b') as f:
                with Image.open(f) as image:
                    cover = resizeimage.resize_contain(image, [200, 100])
                    cover.save(filename, image.format)

        # If some field are empty
        if surname == "" or name == "" or nickname == "":
            error = "Some fields are empty !"

        else:
            # Check if user already exists
            cur = User.query.filter_by(
                nickname=request.form['nickname']).first()
            if cur:
                error = "This nickname is already used !"
            else:
                # Add the new user to the database
                new_user = User(surname, name, nickname, filename)

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


def compute_ranking():
    """
        This method return a list of users with theirs attributes score
        according to the matchs in the database.
    """

    users = User.query.all()
    for user in users:
        user.set_ranking(1000)
        user.set_number_of_matchs()

    matchs = Match.query.all()

    for match in matchs:
        elo(match.player11, match.player12, match.player21, match.player22,
            match.score_e1, match.score_e2)

    return users


def elo(me, my_friend, my_ennemy1, my_ennemy2, my_score, opponent_score):
    """
        This method update the ranking of each players in parameters
        with the socre of the match with the following formula :

        Rn = Ro + KG(W-We)

        @link : https://fr.wikipedia.org
                /wiki/Classement_mondial_de_football_Elo
    """
    # Create fictive player1
    if my_friend is None:
        elo1 = me.ranking
        number_match1 = me.number_of_match
    else:
        elo1 = (me.ranking+my_friend.ranking)/2
        number_match1 = (me.number_of_match+my_friend.number_of_match)/2

    # Create fictive player2
    if my_ennemy2 is None:
        elo2 = my_ennemy1.ranking
        number_match2 = my_ennemy1.number_of_match
    else:
        elo2 = (my_ennemy1.ranking+my_ennemy2.ranking)/2
        number_match2 = (my_ennemy1.number_of_match +
                         my_ennemy2.number_of_match)/2

    # Score for player1
    We1 = p(my_score-opponent_score)
    K = choose_k(number_match1, elo1)
    G = choose_g(my_score, opponent_score)
    W = choose_w(my_score, opponent_score)
    score_p1 = K*G*(W-We1)

    # Score for player2
    We2 = 1 - We1
    K = choose_k(number_match2, elo2)
    G = choose_g(opponent_score, my_score)
    W = choose_w(opponent_score, my_score)
    score_p2 = K*G*(W-We2)

    # Get points to real users
    if my_friend is None:
        me.ranking += int(round(score_p1, 0))
        me.number_of_match += 1
    else:
        sum_ranking = me.ranking+my_friend.ranking
        # update my score
        me.ranking += int(round((me.ranking/sum_ranking)*score_p1, 0))
        me.number_of_match += 1
        # update my friend score
        my_friend.ranking += (
            int(round((my_friend.ranking/sum_ranking)*score_p1, 0)))
        my_friend.number_of_match += 1

    if my_ennemy2 is None:
        my_ennemy1.ranking += int(round((score_p2), 0))
        my_ennemy1.number_of_match += 1
    else:
        sum_ranking = my_ennemy1.ranking+my_ennemy2.ranking
        # update my score
        my_ennemy1.ranking += (
            int(round((my_ennemy1.ranking/sum_ranking)*score_p2, 0)))
        my_ennemy1.number_of_match += 1
        # update my friend score
        my_ennemy2.ranking += (
            int(round((my_ennemy2.ranking/sum_ranking)*score_p2, 0)))
        my_ennemy2.number_of_match += 1


def choose_k(number_of_match, elo):
    """
        Choose the coefficient K, to know if the player is a new player
        or an expert.
    """
    if number_of_match < 40:
        return 40
    elif elo < 2400:
        return 20
    else:
        return 10


def choose_g(score_e1, score_e2):
    """ Choose the correct G (goal difference) coefficient. """
    diff = abs(score_e1 - score_e2)
    if diff < 2:
        G = 1
    elif diff == 2:
        G = 1+1/2
    elif diff == 3:
        G = 1+3/4
    else:
        G = 1+3/4+(diff-3)/8
    return G


def choose_w(score_e1, score_e2):
    """ Choose W coefficient. (Winner or not)"""
    return 1 if score_e1 > score_e2 else 0


def p(i):
    """ Helper method for elo scoring."""
    return 1/(1+10**(-i/400))


def generate_tournament(participants):
    """
        Create a tournament with the participants given in parameter.
    """
    number_of_participants = len(participants)
    if number_of_participants % 2 != 0:
        raise Exception("You must be a power of 2 !")

    # get the list of all players
    players = participants

    # ordered the list of all players
    players = sorted(players, key=lambda player: player.ranking)

    # create the team
    teams = [(players[i], players[len(players)-1-i])
             for i in range(math.floor(len(players)/2))]

    # ordered the team
    teams = sorted(teams, key=lambda team: (team[0].ranking+team[1].ranking)/2)

    index = 1
    for team in teams:
        index += 1

    tournament_head = []
    tournament_queue = []
    first = True
    # create the tournament to make distance between contenders
    for i in range(math.floor(len(teams)/2)):
        if first:
            tournament_head.append(((teams[i]), teams[len(teams)-1-i]))
        else:
            tournament_queue.insert(0, ((teams[i]), teams[len(teams)-1-i]))
        first = not first

    tournament = tournament_head + tournament_queue
    return tournament


def all_pairs(lst):
    """
        Give all pairs possible with the list.
    """
    if len(lst) < 2:
        yield lst
        return
    a = lst[0]
    for i in range(1, len(lst)):
        pair = (a, lst[i])
        for rest in all_pairs(lst[1:i]+lst[i+1:]):
            yield [pair] + rest


def build_avg_temp(pairs, participants):
    """
        Create a array with the average elo for each team
    """
    avg_array = []
    for pair in pairs:
        temp_avg = (
            (participants[pair[0]].ranking+participants[pair[1]].ranking)/2)
        avg_array.append(temp_avg)
    return avg_array


def get_ranking_at_timet(date):
    """
        This method generate a dict with date as key and list of user
        as values. Use this method to generate a chart of the ranking
        evolution.
    """
    date_score = {}

    # Compute the elo at time date
    users = User.query.all()
    for user in users:
        user.set_ranking(1000)
        user.set_number_of_matchs()

    matchs = Match.query.filter(Match.date < date).all()

    for match in matchs:
        elo(match.player11, match.player12, match.player21, match.player22,
            match.score_e1, match.score_e2)

    date_score[date] = deepcopy(users)

    # Get the match per month
    matchs = Match.query.filter(Match.date >= date).all()

    groups_match = groupby(matchs, key=lambda x: x.date.timetuple().tm_mon)

    for month, match_per_month in groups_match:
        if date.month > month:
            date = date.replace(year=date.year+1)
        date = date.replace(month=month)
        for match in match_per_month:
            elo(match.player11, match.player12, match.player21, match.player22,
                match.score_e1, match.score_e2)
        date_score[date] = deepcopy(users)
    return date_score


def init_db():
    """ Initialize the database. """
    db.create_all()

if __name__ == '__main__':
    app.run()
