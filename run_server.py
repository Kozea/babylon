# all the imports
from flask import request, render_template, Flask, make_response
from datetime import datetime
import pygal
import math
from itertools import groupby
from copy import deepcopy
from collections import OrderedDict
from flask_sqlalchemy import SQLAlchemy
from plainform import *
from wtforms.validators import InputRequired, ValidationError
import urllib
import hashlib


# configuration
DEBUG = True
SECRET_KEY = 'development key'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/babylone.db'
db = SQLAlchemy(app)


class Unique(object):
    """ validator that checks field uniqueness """
    def __init__(self, model, field, message=None):
        self.model = model
        self.field = field
        if not message:
            message = u'this user already exists'
        self.message = message

    def __call__(self, form, field):
        if field.object_data == field.data:
            return
        check = DBSession.query(model).filter(field == data).first()
        if check:
            raise ValidationError(self.message)


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
    """ This class represent a user in database with some attributes."""
    id_user = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(100))
    name = db.Column(db.String(100))
    nickname = db.Column(db.String(100), unique=True)
    photo = db.Column(db.String(400))

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
        """ Return the full name of a user."""
        return self.surname+" "+self.name

    def set_ranking(self, ranking):
        """ Set the ranking of a user."""
        self.ranking = ranking

    def set_number_of_matchs(self):
        """ Init the number of match."""
        self.number_of_match = 0


class UserSubscribeForm(Form):
    """This class implements forms for registering new users"""

    def validate_nickname(form, field):
        users = User.query.all()
        for user in users:
            if user.nickname == field.data:
                raise ValidationError('Nickname already exists !')

    surname = StringField('Surname', [InputRequired()])
    name = StringField('Name', [InputRequired()])
    nickname = StringField('Nickname', [validate_nickname, InputRequired()])
    photo = StringField('Gravatar email')
    submit = SubmitField('Validate')


class MatchCreateForm(Form):
    """This class implement forms for creating new matches"""
    def validate_team1(form, field):
        if len(field.data) > 2 or len(field.data) == 0:
            raise ValidationError("Please select 1 or 2 players")

    def validate_team2(form, field):
        if len(field.data) > 2 or len(field.data) == 0:
            raise ValidationError("Please select 1 or 2 players")

        for player_team2 in field.data:
            for player_team1 in form.team1.data:
                if player_team2 == player_team1:
                    raise ValidationError("Please select different users")

    team1 = SelectMultipleField('Team 1', [validate_team1],
                                coerce=int, choices=[])
    team2 = SelectMultipleField('Team 2', [validate_team2],
                                coerce=int, choices=[])

    score_team1 = StringField('Score Team 1', [InputRequired()])
    score_team2 = StringField('Score Team 2', [InputRequired()])
    submit = SubmitField('Validate')

    def __init__(self, *args, **kwargs):
        users = User.query.all()
        user_pairs = []
        for user in users:
            user_tuple = (user.id_user, user.name + ' ' + user.surname)
            user_pairs.append(user_tuple)
        self.team1.kwargs['choices'] = user_pairs
        self.team2.kwargs['choices'] = user_pairs

        Form.__init__(self, *args, **kwargs)


class TournamentForm(Form):
    """ This class implements forms for creating tournament."""
    players = SelectMultipleField('Players', choices=[])
    submit = SubmitField('Validate')


@app.route('/')
def matchs():
    """Querying for all matchs in the database."""
    matchs = Match.query.order_by(-Match.id_match).all()
    return render_template('match.html', matchs=matchs,
                           get_gravatar_url=get_gravatar_url)


@app.route('/svg_victory/<int:id_player>')
def svg_victory(id_player):
    """ Querying for the ranking informations for the different chart. """
    # Never NEVER delete this line because it update score and number of match.
    unordered_ranking = compute_ranking()

    user = User.query.filter(User.id_user == id_player).one()
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
    svg = user.ratio_gauge.render()
    response = make_response(svg)
    response.content_type = 'image/svg+xml'
    return response


@app.route('/ranking')
def ranking():
    """ Querying for the ranking informations for the different chart. """
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

    return render_template('ranking.html', users=ordered_ranking,
                           get_gravatar_url=get_gravatar_url)


def get_gravatar_url(email):
    """Return the gravatar url for the email in parameter."""
    photo = email
    # If there is encoding problem here, it's YOUR fault."
    default = "http://urlz.fr/3z9I"
    size = 150
    gravatar_url = ("http://www.gravatar.com/avatar/" +
                    hashlib.md5(photo.lower()).hexdigest() + "?")
    gravatar_url += urllib.parse.urlencode({'d': default, 's': str(size)})
    return gravatar_url


@app.route('/tournament', methods=['GET', 'POST'])
def tournament():
    """Called when trying to create a tournament."""
    form = TournamentForm(request.form)
    users = compute_ranking()
    user_pairs = []
    for user in users:
        user_tuple = (user.id_user, user.name + ' ' + user.surname)
        user_pairs.append(user_tuple)
    form.players.choices = user_pairs

    if request.method == 'POST':
        players = []
        for id_player in form.players.data:
            players.append(users[int(id_player)-1])
        tournament = generate_tournament(players)

        return render_template(
            'tournament.html', users=users, tournament=tournament,
            get_gravatar_url=get_gravatar_url, form=form())

    return render_template(
        'tournament.html', users=users, form=form())


@app.route('/ranking_graph')
def ranking_graph():
    """Draw the ranking chart with a monthly evolution."""
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


@app.route('/add_match', methods=['GET', 'POST'])
def add_match():
    """Creates a new match using values given to the add_match form."""
    users = User.query.all()
    if len(users) == 0:
        success = "There are no players yet !"
        return render_template('add_match.html', success=success,
                               user=True)

    form = MatchCreateForm(request.form)
    error = None
    success = None

    if request.method == 'POST' and form.validate():
        player11 = User.query.filter_by(id_user=form.team1.data[0]).first()

        if len(form.team1.data) == 2:
            player12 = User.query.filter_by(id_user=form.team1.data[1]).first()
        else:
            player12 = None

        player21 = User.query.filter_by(id_user=form.team2.data[0]).first()

        if len(form.team2.data) == 2:
            player22 = User.query.filter_by(id_user=form.team2.data[1]).first()
        else:
            player22 = None

        match = Match(datetime.now(), form.score_team1.data,
                      form.score_team2.data, player11, player12,
                      player21, player22)

        db.session.add(match)
        db.session.commit()

        success = "Match was successfully added "

    return render_template('add_match.html', success=success,
                           error=error, form=form())


@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    """Creates a new user using values given in the add_player form"""
    form = UserSubscribeForm(request.form)
    success = None
    if request.method == 'POST' and form.validate():
        new_user = User(form.surname.data, form.name.data, form.nickname.data,
                        form.photo.data.encode("utf-8"))
        db.session.add(new_user)
        db.session.commit()
        
        success = form.name.data + " " + form.surname.data + " was successfully registered ! "
        

    return render_template('add_player.html', success=success, form=form())


def get_extension_file(filename):
    """Return the extension of a file.

    Keyword argument:
    filename -- The full name of the file
    """

    index = filename.rfind('.')
    return filename[index:]


def allowed_file(filename):
    """ Test to know if a file has a correct extension. s"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def compute_ranking():
    """This method return a list of users with theirs attributes score
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
    """Update the ranking of each players in parameters.

    with the score of the match according to the following formula :
    Rn = Ro + KG(W-We)
    @link : https://fr.wikipedia.org
            /wiki/Classement_mondial_de_football_Elo

    Keyword arguments:
    me -- the user 1 of team 1
    my_friend -- the user 2 of team1 (perhaps None)
    my_ennemy1 -- the user 1 of team2
    my_ennemy2 -- the user 2 of team2 (perhaps None)
    my_score -- the score of team1
    opponent_score -- the score of team2
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
    """Choose the coefficient K, to know if the player is a new player
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
    """ Choose W coefficient. (Winner or not)."""
    return 1 if score_e1 > score_e2 else 0


def p(i):
    """ Helper method for elo scoring."""
    return 1/(1+10**(-i/400))


def generate_tournament(participants):
    """Create a tournament with the participants given in parameter."""
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
    """Give all pairs possible with the list."""
    if len(lst) < 2:
        yield lst
        return
    a = lst[0]
    for i in range(1, len(lst)):
        pair = (a, lst[i])
        for rest in all_pairs(lst[1:i]+lst[i+1:]):
            yield [pair] + rest


def build_avg_temp(pairs, participants):
    """Create a array with the average elo for each team."""
    avg_array = []
    for pair in pairs:
        temp_avg = (
            (participants[pair[0]].ranking+participants[pair[1]].ranking)/2)
        avg_array.append(temp_avg)
    return avg_array


def get_ranking_at_timet(date):
    """Generate data for ranking chart.

    This method generate a dict with date as key and list of user
    as values. Use this method to generate a chart of the ranking
    evolution.

    Keyword argument:
    date -- the starting date of the chart
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
