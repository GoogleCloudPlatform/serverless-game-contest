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

from datetime import datetime
from flask import Flask, redirect, render_template, request
import json
import os
import uuid

from google.cloud import firestore
from google.cloud import pubsub

RESULT_URL = 'https://your-manager-function-url-goes-here'


app = Flask(__name__)


def get_nickname():
    user_id = request.headers.get('x-goog-authenticated-user-id')
    if user_id is None:
        return None

    nicknames = firestore.Client().collection('nicknames')
    user = nicknames.document(user_id).get()

    if user.exists:
        return user.to_dict().get('nickname')
    else:
        return None


def set_nickname(nickname):
    user_id = request.headers.get('x-goog-authenticated-user-id')
    if user_id is None:
        return

    firestore.Client().collection('nicknames').add({
        'nickname': nickname
        }, document_id=user_id)


# Minimal UI - home page shows current results, link to request new player run
@app.route('/', methods=['GET'])
def echo_recent_results():
    results = []

    rounds = firestore.Client().collection('rounds')
    for contest_round in rounds.order_by(
            'timestamp', direction=firestore.Query.DESCENDING
        ).stream():

        round = contest_round.to_dict()
        round['contest_round'] = contest_round.id
        round['runs'] = []

        for run in contest_round.reference.collection('runs').order_by('questioner').stream():
            round['runs'].append(run.to_dict())

        results.append(round)

    page = render_template('index.html', rounds=results)
    return page


# User navigates to a page to ask for a player to be questioned
@app.route('/request-round', methods=['GET'])
def round_form():
    nickname = get_nickname()
    if nickname is None:
        value = ''
        attributes = ''
    else:
        value = nickname
        attributes = "readonly disabled"

    return render_template(
        'round_form.html',
        value=value, attributes=attributes
    )


# User asks for a player to be run by questioner(s)
@app.route('/request-round', methods=['POST'])
def start_round():
    player_url = request.form.get('player_url')
    if player_url is None:
        return 'Bad Request: missing player_url', 400

    nickname = get_nickname()

    if nickname is None:  # Never seen this user, accept submitted nickname
        nickname = request.form.get('nickname')
        if nickname is not None:
            set_nickname(nickname)
        else:
            return 'Bad Request: missing nickname', 400

    # Internal identifiers for tracking results
    contest_round = str(uuid.uuid4())
    secret = str(uuid.uuid4())
    timestamp = datetime.utcnow()

    firestore.Client().collection('rounds').add({
        'nickname': nickname,
        'player_url': player_url,
        'secret': secret,
        'timestamp': timestamp,
        }, document_id=contest_round)

    # Request trial runs by publishing message to all questioners
    publisher = pubsub.PublisherClient()
    topic_name = 'projects/{project_id}/topics/{topic}'.format(
        project_id=os.getenv('GOOGLE_CLOUD_PROJECT'),
        topic='play-a-game'
    )
    payload = {
        'contest_round': contest_round,
        'player_url': player_url,
        'result_url': RESULT_URL,
        'secret': secret
    }
    publisher.publish(topic_name, json.dumps(payload).encode())

    return redirect('/', code=302)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
