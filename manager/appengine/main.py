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

from google.cloud import datastore
from google.cloud import pubsub

import auth


app = Flask(__name__)


# Minimal UI - home page shows current results, link to request new player run
@app.route('/', methods=['GET'])
def echo_recent_results():
    client = datastore.Client()
    query = client.query(kind='Trial', order=['-timestamp'])
    trials = [
        {
            'timestamp': entity['timestamp'].isoformat(),
            'user': entity['user'],
            'player_url': entity['player_url'],
            'key': entity.key,
            'runs': []
        } for entity in query.fetch()
    ]

    for trial in trials:
        query = client.query(
            kind='Result', 
            order=['-questioner'], 
            ancestor=trial['key']
        )
        for entity in query.fetch():
            trial['runs'].append({
                'questioner': entity['questioner'],
                'outcome': entity['outcome'],
                'moves': entity['moves']
            })
    
    page = render_template('index.html', trials=trials)
    return page


# User navigates to a page to ask for a player to be questioned
@app.route('/request-trial', methods=['GET'])
def trial_form():
    return render_template('trial_form.html')


# User asks for a player to be run by questioner(s)
@app.route('/request-trial', methods=['POST'])
def start_trial():
    # Get the real user's email via Cloud IAP, if available
    email = auth.email()

    # Information about requested trial submitted by user
    user = request.form['user']
    player_url = request.form['player_url']

    # Internal identifiers for tracking results
    contest_round = str(uuid.uuid4())
    timestamp = datetime.utcnow()

    # Remember the trial being requested
    client = datastore.Client()
    key = client.key('Trial', contest_round)
    entity = datastore.Entity(key=key)
    entity.update({
        'email': email,
        'user': user,
        'player_url': player_url,
        'timestamp': timestamp
    })
    client.put(entity)

    # Determine the URL for reporting results. Unless Identity Aware Proxy is
    # enabled to restrict access to the App Engine app, that URL can be served
    # by this App Engine instance itself.
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    result_url = 'https://{}.appspot.com/report-result'.format(project_id)

    # If Identity Aware Proxy is activated, the questioner Cloud Functions will
    # not be able to connect to this App Engine app. In that case, a separate
    # Cloud Function will be used to receive and record scores. To enable that,
    # fill in the Cloud Function's URL and uncomment the line below:
    # result_url = 'report-cloud-function-url'

    # Request trial runs by publishing message to all questioners
    publisher = pubsub.PublisherClient()
    topic_name = 'projects/{project_id}/topics/{topic}'.format(
        project_id=os.getenv('GOOGLE_CLOUD_PROJECT'),
        topic='play-a-game'
    )
    payload = {
        'contest_round': contest_round,
        'player_url': player_url,
        'result_url': result_url
    }
    publisher.publish(topic_name, json.dumps(payload).encode())

    # TODO: acknowledge to the user that the trial(s) are pending
    return redirect('/', code=302)


# A questioner reports a result
@app.route('/report-result', methods=['POST'])
def save_result():
    # All result reports should be in JSON form
    result = request.get_json()
    if result is None:
        return 415  # Unsupported media type (not application/json)

    # Reported result data in payload
    contest_round = result['contest_round']
    outcome = result['outcome']
    moves = result['moves']
    questioner = result['questioner']

    # Look up contest_round random ID to be sure this is a genuine report
    client = datastore.Client()
    trial_key = client.key('Trial', contest_round)
    trial_entity = client.get(trial_key)
    if trial_entity is None:
        return 404  # Not found - no such contest_round was ever asked for
    
    # Update results with new data
    result_id = str(uuid.uuid4())
    result_key = client.key('Result', result_id, parent=trial_key)
    result_entity = datastore.Entity(key=result_key)
    result_entity.update({
        'questioner': questioner,
        'outcome': outcome,
        'moves': moves
    })
    client.put(result_entity)
    
    # Acknowledge a successful report
    return 201  # Created (a new contest score entry)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
