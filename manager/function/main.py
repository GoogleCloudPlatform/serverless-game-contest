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

from google.cloud import firestore


def save_result(request):
    # All result reports should be in JSON form
    result = request.get_json()

    # Reported result data in payload
    contest_round = result['contest_round']
    outcome = result['outcome']
    moves = result['moves']
    questioner = result['questioner']
    secret = result['secret']

    # Look up contest_round random ID to be sure this is a genuine report
    db = firestore.Client()
    rounds = db.collection('rounds')

    this_round = rounds.document(contest_round).get()
    if not this_round.exists:
        return '404'  # Not found - no such contest_round was ever asked for
    if secret != this_round.to_dict().get('secret'):
        return '403'  # Forbidden - they don't know the shared secret

    # Update results with new data
    rounds.document(contest_round).collection('runs').add({
        'outcome': outcome,
        'moves': moves
    }, document_id=questioner)

    # Acknowledge a successful report
    return '201'  # Created (a new contest score entry)
