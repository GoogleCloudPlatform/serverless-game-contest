# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import json
import requests

MINIMUM = 1
MAXIMUM = 10
TARGET = 7
MAX_GUESSES = 20
QUESTIONER = 'easy-questioner'


def report_score(url, outcome, moves, contest_round, secret):
    score = {
        'questioner': QUESTIONER,
        'contest_round': contest_round,
        'secret': secret,
        'outcome': outcome,
        'moves': moves
    }
    requests.post(url, data=json.dumps(score),
        headers={'Content-type': 'application/json'}
    )


def play_game(url):
    # Keep track of the plays in this game to provide for each guess
    state = {
        'minimum': MINIMUM,
        'maximum': MAXIMUM,
        'history': []
    }

    # Give the player MAX_GUESSES tries to find the TARGET
    for guess_number in range(1, MAX_GUESSES+1):
        try:
            player_response = requests.post(url, data=json.dumps(state),
                headers={'Content-type': 'application/json'}
            )
            guess = player_response.json()
            if guess == TARGET:
                # Done. Exit loop by returning outcome
                return 'won', guess_number
            if guess < TARGET:
                state['history'].append({'guess': guess, 'result': 'higher'})
            else:
                state['history'].append({'guess': guess, 'result': 'lower'})
        except:
            # Player could not return a valid response
            return 'crashed', guess_number

    # Give up after MAX_GUESSES
    return 'failed', MAX_GUESSES


def question_player(event, context):
    message = json.loads(base64.b64decode(event['data']).decode('utf-8'))
    
    player_url = message['player_url']
    result_url = message['result_url']
    contest_round = message['contest_round']
    secret = message['secret']

    outcome, moves = play_game(player_url)
    report_score(result_url, outcome, moves, contest_round, secret)
