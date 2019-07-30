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

# As of this writing, the standard Python Google Cloud tools can only produce
# a signed URL (so anyone with the URL can access the Cloud Storage object) by
# using a service account key file. We want to use the metadata server to get
# service account credentials instead. The page
# "V4 signing process with your own program" at
# https://cloud.google.com/storage/docs/access-control/signing-urls-manually
# describes how we can do this, and forms the basis of this module.


import binascii
from datetime import datetime
import hashlib
import requests
from urllib.parse import quote

from google.cloud import iam_credentials_v1


def signed_url(bucket_name, blob_name, expires=3600, method='GET', headers={}):

    # The same timestamp is used in several places
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

    # The request must include this host header, so make sure it's there
    headers['host'] = 'storage.googleapis.com'

    # The default service account's email is used in several places
    metadata_url = 'http://metadata.google.internal/computeMetadata/v1/'
    metadata_url += 'instance/service-accounts/default/email'
    response = requests.get(
        metadata_url,
        headers={'Metadata-Flavor': 'Google'}
    )
    email = response.text


    def header_names():
        return sorted([key.lower() for key in headers.keys()])

    def canonical_headers():
        return '\n'.join([
            '{}:{}'.format(key, headers[key]) for key in header_names()
        ])

    def canonical_query_string():
        credential = '{}%2F{}%2Fauto%2Fstorage%2Fgoog4_request'.format(
            quote(email), timestamp[:8]
        )

        queries = [
            'X-Goog-Algorithm=GOOG4-RSA-SHA256',
            'X-Goog-Credential=' + credential,
            'X-Goog-Date={}'.format(timestamp),
            'X-Goog-Expires={}'.format(expires),
            'X-Goog-SignedHeaders=' + ';'.join(header_names())
        ]

        return '&'.join(sorted(queries))

    def canonical_request():
        return '\n'.join([
        method,
        '/{}/{}'.format(bucket_name, blob_name),
        canonical_query_string(),
        canonical_headers(),
        '',
        ';'.join(header_names()),
        'UNSIGNED-PAYLOAD'
    ])

    def string_to_sign():
        return '\n'.join([
            'GOOG4-RSA-SHA256',
            timestamp,
            '{}/auto/storage/goog4_request'.format(timestamp[:8]),
            hashlib.sha256(canonical_request().encode()).hexdigest()
        ])

    client = iam_credentials_v1.IAMCredentialsClient()
    name = 'projects/-/serviceAccounts/{}'.format(email)

    result = client.sign_blob(name, string_to_sign().encode())
    signature = binascii.hexlify(result.signed_blob).decode()

    signed_url = '{}{}?{}&X-Goog-Signature={}'.format(
        'https://storage.googleapis.com/',
        '{}/{}'.format(bucket_name, blob_name),
        canonical_query_string(),
        signature
    )

    return signed_url
