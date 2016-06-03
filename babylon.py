#!/usr/bin/env python

"""
Babylon
=======

1. A significant city in ancient Mesopotamia.
2. A web interface managing table football matches and tournaments.

"""

import hashlib
import urllib
from copy import deepcopy
from datetime import datetime
from itertools import groupby
from collections import OrderedDict

import pygal
from flask import request, render_template, Flask, make_response, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_method
from plainform import Form, StringField, SubmitField, SelectMultipleField
from wtforms.validators import InputRequired, ValidationError


GRAVATAR_DEFAULT = 'http://urlz.fr/3z9I'
GRAVATAR_SIZE = '150'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'development key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/babylone.db'
db = SQLAlchemy(app)

cached_ranking = None


class Match(db.Model):
    """Match table."""
    id_match = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    score_team_1 = db.Column(db.Integer)
    score_team_2 = db.Column(db.Integer)
    team_1_player_1_id = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    team_1_player_2_id = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    team_2_player_1_id = db.Column(db.Integer, db.ForeignKey('user.id_user'))
    team_2_player_2_id = db.Column(db.Integer, db.ForeignKey('user.id_user'))

    team_1_player_1 = db.relationship(
        'User', foreign_keys=[team_1_player_1_id])
    team_2_player_1 = db.relationship(
        'User', foreign_keys=[team_2_player_1_id])
    team_2_player_2 = db.relationship(
        'User', foreign_keys=[team_2_player_2_id])
    team_1_player_2 = db.relationship(
        'User', foreign_keys=[team_1_player_2_id])

    def __init__(self, date, score_team_1, score_team_2, team_1_player_1,
                 team_1_player_2, team_2_player_1, team_2_player_2):
        self.date = date
        self.score_team_1 = score_team_1
        self.score_team_2 = score_team_2
        self.team_1_player_1 = team_1_player_1
        self.team_1_player_2 = team_1_player_2
        self.team_2_player_1 = team_2_player_1
        self.team_2_player_2 = team_2_player_2

        
class User(db.Model):
    """User table."""
    id_user = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String())
    name = db.Column(db.String())
    nickname = db.Column(db.String(), unique=True)
    email = db.Column(db.String())

    def __init__(self, surname, name, nickname, email):
        self.surname = surname
        self.name = name
        self.nickname = nickname
        self.email = email
        self.ranking = -1
        self.number_of_match = 0
        self.nb_victories = 0
        self.nb_defeats = 0
        self.ratio_gauge = None

    @property
    def full_name(self):
        """Full name of the user."""
        return "{} {}".format(self.surname, self.name)

    @property
    def gravatar_url(self):
        """Gravatar URL of the user."""
        return "http://www.gravatar.com/avatar/{}?{}".format(
            hashlib.md5(self.email.lower()).hexdigest(),
            urllib.parse.urlencode(
                                    {'d': GRAVATAR_DEFAULT,
                                     's': GRAVATAR_SIZE})
                                  )

    def teammate(self, match):
        """Return the user's teammate if he exists."""
        teammate = []
        if self == match.team_1_player_1:
            teammate.append(match.team_1_player_2)

        elif self == match.team_1_player_2:
            teammate.append(match.team_1_player_1)

        elif self == match.team_2_player_1:
            teammate.append(match.team_2_player_2)

        elif self == match.team_2_player_2:
            teammate.append(match.team_2_player_1)
        return teammate

    def opponents(self, match):
        """Return one player's opponent(s) in a match."""
        opponents = []

        if self == match.team_1_player_1 or self == match.team_1_player_2:
            opponents.append(match.team_2_player_1)
            if match.team_2_player_2 is not None:
                opponents.append(match.team_2_player_2)
        else:
            opponents.append(match.team_1_player_1)
            if match.team_1_player_2 is not None:
                opponents.append(match.team_1_player_2)

        return opponents


class UserSubscribeForm(Form):
    """Form registering new users."""
    def validate_nickname(form, field):
        """Validate the uniqueness of the nickname."""
        users = User.query.all()
        for user in users:
            if user.nickname == field.data:
                raise ValidationError('Nickname already exists !')

    surname = StringField('Surname', [InputRequired()])
    name = StringField('Name', [InputRequired()])
    nickname = StringField('Nickname', [validate_nickname, InputRequired()])
    email = StringField('Gravatar email')
    submit = SubmitField('Create Player !')


class TournamentForm(Form):
    """Form creating tournaments."""
    players = SelectMultipleField('Players', choices=[])
    submit = SubmitField('Validate')


@app.route('/')
def matchs():
    """Query all the matchs, more recents first."""
    matchs = Match.query.order_by(-Match.id_match).all()
    if not matchs:
        flash("There are no matchs yet !")
    return render_template('match.html', matchs=matchs)


@app.route('/profile/<int:id_player>')
def profile(id_player):
    """Query detailled informations about one player from its id."""
    unordered_ranking = compute_ranking()

    user = None
    for temp_user in unordered_ranking:
        if temp_user.id_user == id_player:
            user = temp_user
            break

    nemesis, nemesis_coeff = get_related_player(user, True, True)
    best_teammate, best_teammate_coeff = get_related_player(user, True, False)
    worst_teammate, worst_teammate_coeff = get_related_player(user, False, False)
    matchs = get_matchs(user)

    victories_as_team1 = (
        db.session.query(Match.id_match)
        .filter((Match.team_1_player_1 == user) |
                (Match.team_1_player_2 == user))
        .filter(Match.score_team_1 > Match.score_team_2)
        .count())
    victories_as_team2 = (
        db.session.query(Match.id_match)
        .filter((Match.team_2_player_1 == user) |
                (Match.team_2_player_2 == user))
        .filter(Match.score_team_1 < Match.score_team_2)
        .count())

    user.nb_victories = victories_as_team1 + victories_as_team2
    user.nb_defeats = user.number_of_match - user.nb_victories

    return render_template(
        'profile.html', user=user, nemesis=nemesis,
        nemesis_coeff=nemesis_coeff, best_teammate=best_teammate,
        worst_teammate=worst_teammate, best_teammate_coeff=best_teammate_coeff,
        worst_teammate_coeff=worst_teammate_coeff, matchs=matchs)


@app.route('/svg_victory/<int:id_player>')
def svg_victory(id_player):
    """Query ranking informations for one player from its id."""
    unordered_ranking = compute_ranking()

    user = None
    for temp_user in unordered_ranking:
        if temp_user.id_user == id_player:
            user = temp_user
            break

    victories_as_team1 = (
        db.session.query(Match.id_match)
        .filter((Match.team_1_player_1 == user) |
                (Match.team_1_player_2 == user))
        .filter(Match.score_team_1 > Match.score_team_2)
        .count())
    victories_as_team2 = (
        db.session.query(Match.id_match)
        .filter((Match.team_2_player_1 == user) |
                (Match.team_2_player_2 == user))
        .filter(Match.score_team_1 < Match.score_team_2)
        .count())

    user.nb_victories = victories_as_team1 + victories_as_team2
    user.nb_defeats = user.number_of_match - user.nb_victories

    if user.number_of_match != 0:
        gauge = pygal.SolidGauge(inner_radius=0.70, show_legend=False)
        gauge.value_formatter = lambda x: '{:.0f}%'.format(x)
        gauge.add(
            'Ratio', [{
                'value': (user.nb_victories/user.number_of_match)*100,
                'max_value': 100}])
        
    svg = gauge.render()
    response = make_response(svg)
    response.content_type = 'image/svg+xml'
    return response


@app.route('/ranking')
def ranking():
    """Query the ranking informations. """
    users = User.query.all()
    if not users:
        flash("There are no players yet !")
        return render_template('ranking.html')

    unordered_ranking = compute_ranking()

    for user in unordered_ranking:
        victories_as_team1 = (
            db.session.query(Match.id_match)
            .filter((Match.team_1_player_1 == user) |
                    (Match.team_1_player_2 == user))
            .filter(Match.score_team_1 > Match.score_team_2)
            .count())
        victories_as_team2 = (
            db.session.query(Match.id_match)
            .filter((Match.team_2_player_1 == user) |
                    (Match.team_2_player_2 == user))
            .filter(Match.score_team_1 < Match.score_team_2)
            .count())

        user.nb_victories = victories_as_team1 + victories_as_team2
        user.nb_defeats = user.number_of_match - user.nb_victories

    ordered_ranking = sorted(
        unordered_ranking, key=lambda user: -user.ranking)

    return render_template('ranking.html', users=ordered_ranking)


@app.route('/tournament', methods=['GET', 'POST'])
def tournament():
    """Create a tournament."""
    users = User.query.all()
    if not users:
        flash("There are no players yet !")
        return render_template('tournament.html')

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
            'tournament.html', users=users, tournament=tournament, form=form())

    return render_template(
        'tournament.html', users=users, form=form())


@app.route('/ranking_graph')
def ranking_graph():
    """Draw the ranking chart with a monthly evolution."""
    return render_template('ranking_graph.html')


@app.route('/render_ranking_graph')
def render_ranking_graph():
    """Render the svg file for monthly evolution."""
    now = datetime.now()
    if now.month-5 != 0:
        date = now.replace(month=now.month-5)
    else:
        date = now.replace(month=12).replace(year=now.year-1)
    date_score = OrderedDict(sorted(get_ranking(date).items()))
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
        line_chart.add(user_base.full_name, user_array)
    svg = line_chart.render()
    response = make_response(svg)
    response.content_type = 'image/svg+xml'
    return response


@app.route('/add_match', methods=['GET', 'POST'])
def add_match():
    """Create a new match."""
    users = User.query.all()
    if not users:
        flash("There are no players yet !")
        return render_template('add_match.html', users=users)

    error = None
    success = None

    if request.method == 'POST':
        param_list = request.form.to_dict().keys()

        id_team_1_player_1 = request.form["j11"][7:]
        team_1_player_1 = User.query.filter_by(
            id_user=id_team_1_player_1).first()

        if "j12" in param_list:
            id_team_1_player_2 = request.form["j12"][7:]
            team_1_player_2 = User.query.filter_by(
                id_user=id_team_1_player_2).first()
        else:
            team_1_player_2 = None

        id_team_2_player_1 = request.form["j21"][7:]
        team_2_player_1 = User.query.filter_by(
            id_user=id_team_2_player_1).first()

        if "j22" in param_list:
            id_team_2_player_2 = request.form["j22"][7:]
            team_2_player_2 = User.query.filter_by(
                id_user=id_team_2_player_2).first()
        else:
            team_2_player_2 = None

        match = Match(
            datetime.now(), request.form["scoret1"], request.form["scoret2"],
            team_1_player_1, team_1_player_2, team_2_player_1, team_2_player_2)

        db.session.add(match)
        db.session.commit()
        global cached_ranking
        cached_ranking = None

        flash("Match was successfully added ")

    return render_template(
        'add_match.html', users=users, success=success, error=error)


@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    """Create a new user."""
    form = UserSubscribeForm(request.form)
    if request.method == 'POST' and form.validate():
        new_user = User(
            form.surname.data, form.name.data, form.nickname.data,
            form.email.data.encode("utf-8"))
        db.session.add(new_user)
        db.session.commit()

        flash(form.name.data + ' ' + form.surname.data +
              " was successfully registered")

    return render_template('add_player.html', form=form())


def compute_ranking():
    """Get the list of all users with their current score."""
    if cached_ranking is None:
        users = User.query.all()
        for user in users:
            user.ranking = 1000
            user.number_of_match = 0

        matchs = Match.query.all()
        for match in matchs:
            elo(match.team_1_player_1, match.team_1_player_2,
                match.team_2_player_1, match.team_2_player_2,
                match.score_team_1, match.score_team_2)
        return users
    else:
        return cached_ranking


def elo(team_1_player_1, team_1_player_2, team_2_player_1, team_2_player_2,
        score_team_1, score_team_2):
    """Update the ranking of each players in parameters.

    Calculate the score of the match according to the following formula:
    Rn = Ro + KG (W - We)

    See: https://fr.wikipedia.org /wiki/Classement_mondial_de_football_Elo

    """
    # Create fictive player1
    if team_1_player_2 is None:
        elo1 = team_1_player_1.ranking
        number_match1 = team_1_player_1.number_of_match
    else:
        elo1 = (team_1_player_1.ranking + team_1_player_2.ranking) / 2
        number_match1 = (
            team_1_player_1.number_of_match +
            team_1_player_2.number_of_match) / 2

    # Create fictive player2
    if team_2_player_2 is None:
        elo2 = team_2_player_1.ranking
        number_match2 = team_2_player_1.number_of_match
    else:
        elo2 = (team_2_player_1.ranking + team_2_player_2.ranking) / 2
        number_match2 = (
            team_2_player_1.number_of_match +
            team_2_player_2.number_of_match) / 2

    # Score for player1
    expected_result = 1 / (1 + 10 ** ((score_team_2 - score_team_1) / 400))
    expertise = get_expertise_coefficient(number_match1, elo1)
    goal_difference = get_goal_difference_coefficient(
        score_team_1, score_team_2)
    result = 1 if score_team_1 > score_team_2 else 0
    score_p1 = expertise * goal_difference * (result - expected_result)

    # Score for player2
    expected_result = 1 - expected_result
    expertise = get_expertise_coefficient(number_match2, elo2)
    goal_difference = get_goal_difference_coefficient(
        score_team_2, score_team_1)
    result = 1 if score_team_1 < score_team_2 else 0
    score_p2 = expertise * goal_difference * (result - expected_result)

    # Update the ranking and the number of matches of the users
    team_1_player_1.number_of_match += 1
    if team_1_player_2 is None:
        team_1_player_1.ranking += round(score_p1)
    else:
        sum_ranking = team_1_player_1.ranking + team_1_player_2.ranking
        team_1_player_1.ranking += round(
            team_1_player_1.ranking / sum_ranking * score_p1)
        team_1_player_2.ranking += round(
            team_1_player_2.ranking / sum_ranking * score_p1)
        team_1_player_2.number_of_match += 1

    team_2_player_1.number_of_match += 1
    if team_2_player_2 is None:
        team_2_player_1.ranking += round(score_p2)
    else:
        sum_ranking = team_2_player_1.ranking + team_2_player_2.ranking
        team_2_player_1.ranking += round(
            team_2_player_1.ranking / sum_ranking * score_p2)
        team_2_player_2.ranking += round(
            team_2_player_2.ranking / sum_ranking * score_p2)
        team_2_player_2.number_of_match += 1


def get_expertise_coefficient(number_of_match, elo):
    """Get expertise coefficient corresponding to an user's elo and matches."""
    if number_of_match < 40:
        return 40
    elif elo < 2400:
        return 20
    else:
        return 10


def get_goal_difference_coefficient(score_team_1, score_team_2):
    """Get goal difference coefficient corresponding to a match score."""
    diff = abs(score_team_1 - score_team_2)
    if diff < 2:
        return 1
    elif diff == 2:
        return 1.5
    elif diff == 3:
        return 1.75
    else:
        return 1.75 + (diff - 3) / 8


def generate_tournament(players):
    """Create a tournament with the given players."""
    if len(players) < 4 or bin(len(players)).count('1') != 1:
        raise ValueError('The number of players must be a power of 2')

    players.sort(key=lambda player: player.ranking)
    teams = []
    while players:
        teams.append([players.pop(0), players.pop(-1)])
    teams.sort(key=lambda team: team[0].ranking + team[1].ranking)
    tournament = []
    while teams:
        tournament.append([teams.pop(0), teams.pop(-1)])
    return tournament


def get_matchs(player, team_match=False, win=None):
    """Get a list of all matchs involving a given player."""
    comparison = lambda x,y :((x>y if win is True else  x<y) if win is not None else True)
    test_team = lambda x,y : (y != None if x else True)
    query = Match.query.filter(
        ((((Match.team_1_player_1 == player) |
          (Match.team_1_player_2 == player)) &
          test_team(team_match, Match.team_1_player_2) &
          (comparison(Match.score_team_1, Match.score_team_2))) |
         (((Match.team_2_player_1 == player) |
          (Match.team_2_player_2 == player)) &
          test_team(team_match, Match.team_2_player_2) &
          (comparison(Match.score_team_2, Match.score_team_1)))))
        
    return query.order_by(-Match.id_match).all()


def get_related_player(player, best=True, nemesis=False):
    """Get a player's worst teammates.

    A player is another player's worst teammate when he lost the most with him,
    while playing as a team.

    """
    matchs = get_matchs(player, not nemesis, best and not nemesis)
    teammates = {}

    for match in matchs:
        if nemesis:
            player_teammate = player.opponents(match)
        else:
            player_teammate = player.teammate(match)
        for player_related in player_teammate:
            if player_related:
                if player_related in teammates:
                    teammates[player_related] += 1
                else:
                    teammates[player_related] = 1

    teammate = []
    max_score = 0
    if teammates:
        max_score = max(teammates.values())
        teammate = [player_temp for player_temp, max_s
                    in teammates.items() if max_s == max_score]
    return teammate, max_score


def get_ranking(date):
    """Generate data for ranking chart.

    This method generate a dict with date as key and list of user as
    values. Use this method to generate a chart of the ranking evolution.

    """

    date_score = {}

    # Compute the elo at time date
    users = User.query.all()
    for user in users:
        user.ranking = 1000
        user.number_of_match = 0

    matchs = Match.query.filter(Match.date < date).all()

    for match in matchs:
        elo(match.team_1_player_1, match.team_1_player_2,
            match.team_2_player_1, match.team_2_player_2,
            match.score_team_1, match.score_team_2)

    date_score[date] = deepcopy(users)

    # Get the match per month
    matchs = Match.query.filter(Match.date >= date).all()

    groups_match = groupby(matchs, key=lambda x: x.date.timetuple().tm_mon)

    for month, match_per_month in groups_match:
        if date.month > month:
            date = date.replace(year=date.year+1)
        date = date.replace(month=month)
        for match in match_per_month:
            elo(match.team_1_player_1, match.team_1_player_2,
                match.team_2_player_1, match.team_2_player_2,
                match.score_team_1, match.score_team_2)
        date_score[date] = deepcopy(users)
    return date_score

if __name__ == '__main__':
    app.run(debug=True)
