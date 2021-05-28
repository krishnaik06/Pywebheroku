from pywebio.platform.flask import webio_view
from pywebio import STATIC_PATH
from flask import Flask, send_from_directory
from pywebio.input import *
from pywebio.output import *
import argparse
from pywebio import start_server
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd

np.random.seed(1)

ab_testing_challenge = Flask(__name__)
number_of_trials = 6000


# defining the bandit set up
class ABBandit:
    def __init__(self):
        # general setup
        self.reward_per_win = 0.40
        self.bandits = ['A', 'B', 'C']
        self.played = {'A': 0,
                       'B': 0,
                       'C': 0}
        self.wins = {'A': 0,
                     'B': 0,
                     'C': 0}
        self.actual_win_rate = {'A': 0.03,
                                'B': 0.02,
                                'C': 0.035}
        self.observed_win_rate = {'A': 0.0,
                                  'B': 0.0,
                                  'C': 0.0}
        self.money_won = {'A': 0.0,
                          'B': 0.0,
                          'C': 0.0}
        self.overall_played = 0
        self.overall_wins = 0
        self.overall_winrate = 0
        self.overall_money_won = 0
        self.games_left = number_of_trials
        # prior/posterior believes
        self.pri_post_a = {'A': 1,
                           'B': 1,
                           'C': 1}
        self.pri_post_b = {'A': 1,
                           'B': 1,
                           'C': 1}

    def sample(self, bandit):
        return np.random.beta(self.pri_post_a[bandit], self.pri_post_b[bandit])

    def pull_arm(self, bandit, rounds, mode='Human'):
        if mode == 'Thompson sampling':
            # Thompson sampling
            bandits_prob = np.argmax([self.sample(b) for b in self.bandits])
            bandit = self.bandits[bandits_prob]
        else:
            pass
        for i in range(rounds):
            if self.games_left > 0:
                random_chance = np.random.rand()
                self.played[bandit] += 1
                self.overall_played += 1
                if random_chance < self.actual_win_rate[bandit]:
                    self.wins[bandit] += 1
                    self.overall_wins += 1
                    self.pri_post_a[bandit] += 1
                else:
                    self.pri_post_b[bandit] += 1
                self.observed_win_rate[bandit] = self.wins[bandit] / self.played[bandit]
                self.money_won[bandit] = self.wins[bandit] * self.reward_per_win
                self.overall_winrate = self.overall_wins / self.overall_played
                self.overall_money_won = self.overall_wins * self.reward_per_win
                self.games_left = number_of_trials - self.overall_played
            else:
                pass
        # update df_overview
        core_data = {'Bandits': list(bandit_challenge.bandits),
                     'Played': list(bandit_challenge.played.values()),
                     'Wins': list(bandit_challenge.wins.values()),
                     'Winrate': list(bandit_challenge.observed_win_rate.values())
                     }
        df_overview = pd.DataFrame(core_data, columns=['Bandits', 'Played', 'Wins', 'Winrate'])
        return df_overview


def generate_bar_charts(df, x_axis, y_axis, title):
    fig = px.bar(df, x=x_axis, y=y_axis,
                 color=y_axis,
                 height=400)
    fig.update_layout(title_text=title)
    html = fig.to_html(include_plotlyjs="require", full_html=False)
    return put_html(html).send()


# instantiate bandits
bandit_challenge = ABBandit()
run_web_page = True


def run_experiment(page=True):
    run_web_page = page
    while run_web_page:
        add_more = True

        while add_more:
            add_more = actions(label="Which bandit do you chose?",
                               buttons=[{'label': 'A', 'value': 'A'},
                                        {'label': 'B', 'value': 'B'},
                                        {'label': 'C', 'value': 'C'},
                                        {'label': 'Thompson sampling', 'value': 'Thompson sampling'}])
            if add_more == 'Thompson sampling':
                rounds = 1
                for i in range(bandit_challenge.games_left):
                    df_overview = bandit_challenge.pull_arm(add_more, rounds, mode='Thompson sampling')
            else:
                rounds = input("How many rounds do you want to play?", value='1', type=NUMBER)
                df_overview = bandit_challenge.pull_arm(add_more, rounds, mode='Human')
            # show total money won
            fig = go.Figure(go.Indicator(
                mode="number",
                value=bandit_challenge.overall_money_won,
                domain={'x': [0.1, 1], 'y': [0.2, 0.9]},
                title={'text': "Money won so far:"}))
            html = fig.to_html(include_plotlyjs="require", full_html=False)
            put_html(html).send()
            # show progress and rounds left
            fig = go.Figure(go.Indicator(
                mode="number+gauge+delta",
                gauge={'shape': "bullet"},
                delta={'reference': number_of_trials},
                value=df_overview['Played'].sum(),
                domain={'x': [0.1, 1], 'y': [0.2, 0.9]},
                title={'text': "No. played"}))
            html = fig.to_html(include_plotlyjs="require", full_html=False)
            put_html(html).send()

            generate_bar_charts(df_overview, 'Bandits', 'Played', 'Rounds played')
            generate_bar_charts(df_overview, 'Bandits', 'Winrate', 'Overview of winrates')

            continue_button = actions(label="Do you want to continue",
                                      buttons=[{'label': 'Yes', 'value': True},
                                               {'label': 'No', 'value': False}])
            if continue_button:
                clear()
            else:
                add_more = False


ab_testing_challenge.add_url_rule('/tool', 'webio_view', webio_view(run_experiment),
                                  methods=['GET', 'POST', 'OPTIONS'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=8080)
    args = parser.parse_args()

    start_server(run_experiment, port=args.port)
