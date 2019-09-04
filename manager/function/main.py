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


""" The save_result cloud function is invoked via HTTP request containing a
    JSON body. If the contents of the body are acceptable, the result data
    is saved in a Cloud Firestore database, which is used by the manager
    app to display standings.

    Fields expected in the request's JSON body:

    contest_round - the identifier of this "round" (exercising the submitted
        player via one or more questioners)

    outcome - whether the player 'won', 'lost', 'crashed', or 'failed' (did
        not finish)

    moves - the number of moves the game took

    questioner - the name of the questioner, e.g., easy, hard, etc.

    secret - the secret that was provided to the questioner when it was
        invoked, used to make sure that imposters don't post false results
"""

import json
from google.cloud import firestore


def save_result(request):
    # All result reports should be in JSON form
    result = request.get_json()

    # Reported result data is the request payload
    contest_round = result['contest_round']
    outcome = result['outcome']
    moves = result['moves']
    questioner = result['questioner']
    secret = result['secret']

    # Look up contest_round random ID to be sure this is a genuine report
    rounds = firestore.Client().collection('rounds')
    this_round = rounds.document(contest_round).get()

    if not this_round.exists:
        return '404'  # Not found - no such contest_round was ever asked for
    if secret != this_round.to_dict().get('secret'):
        return '403'  # Forbidden - they don't know the shared secret

    # Update results with data from this new run
    rounds.document(contest_round).collection('runs').add({
        'outcome': outcome,
        'moves': moves,
        'questioner': questioner,
    })

    # Acknowledge a successful report
    return '201'  # Created (a new contest run entry)
