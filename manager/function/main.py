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
import json
import os
import uuid

from google.cloud import datastore
from google.cloud import pubsub


def save_result(request):
    # All result reports should be in JSON form
    result = request.get_json()

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
