from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session
import requests
import json
from contextlib import contextmanager

from os.path import join, dirname
from dotenv import load_dotenv
import os

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

client_id = os.environ.get("PODIO_CLIENT_ID")
client_secret = os.environ.get("PODIO_CLIENT_SECRET")
username = os.environ.get("PODIO_USERNAME")
password = os.environ.get("PODIO_PASSWORD")

if client_id is None:
    raise Exception("please copy .env.sample to .env and fill in the fields you need")


def get_token(id, secret, user, pw):
    oauth = OAuth2Session(client=LegacyApplicationClient(client_id=id))
    token = oauth.fetch_token(token_url='https://api.podio.com/oauth/token', username=user, password=pw,
                              client_id=id, client_secret=secret)
    return token['access_token']


@contextmanager
def podio_api():
    with requests.Session() as podio_client:
        token = get_token(client_id, client_secret, username, password)
        podio_client.headers = {'Authorization': 'OAuth2 ' + token}
        yield podio_client


def user_data(api):
    response = api.get('https://api.podio.com/item/app/11575728/', params={'limit': 200})  # must be a limit, default 20
    if response.status_code != 200:
        raise Exception('non 200 getting users', response)

    return_value = {}
    for item in json.loads(response.text)['items']:
        user_dict = {
            # hack.. because start data doesn't have value but rest do
            field['label']: field['values'][0].get('value', field['values'][0]) for field in item['fields']
        }
        return_value[user_dict['Name']] = user_dict  # use name as the key for now?
    return return_value


def apps(api):
    response = api.get('https://api.podio.com/app/', params={'limit': 100})  # must be a limit, max 100
    if response.status_code != 200:
        raise Exception('non 200 getting apps', response)

    return json.loads(response.text)


def post_to_corp_news(api, title, text):
    fields = {
        'title': str(title),
        'bulletin-text': str(text)
    }
    # response = api.post('https://api.podio.com/item/app/11533074/', json={'fields': fields})
    response = api.post('https://api.podio.com/item/app/11533074/', json={'fields': fields}, params={'silent': True, "hook": False})
    if response.status_code != 200:
        raise Exception('non 200 getting apps', response)
    return json.loads(response.text)


def corp_news(api, limit=1):
    response = api.get('https://api.podio.com/item/app/11533074/', params={'limit': limit})
    if response.status_code != 200:
        raise Exception('non 200 getting apps', response)
    return json.loads(response.text)


# useful to print out all the user apps
def print_apps():
    with podio_api() as api:
        for app in apps(api):
            print(f"{app['app_id']} {app['config']['name']} {app['link']}")


# useful to list out app fields
def print_app_fields(app_id):
    with podio_api() as api:
        response = api.get(f'https://api.podio.com/app/{app_id}')
        if response.status_code != 200:
            raise Exception('non 200 getting app fields', response)
        # print(json.loads(response.text)['fields'])
        for field in json.loads(response.text)['fields']:
            print(f"{field['external_id']}")


if __name__ == "__main__":
    # print_apps()
    # print_app_fields(11533074)
    with podio_api() as api:
        #this just lists all users and their bdays etc...
        for name, data in sorted(user_data(api).items(), key=lambda x: x[0]):
            print(f"{name} started: {data.get('Start Date',[]).get('start_utc')} born: {data.get('Birth Date (mm/dd)')}")

        # this posts to the corp news... probably need to add to this method to tag etc...
        # post_to_corp_news(api, 'Testing', 'This is just a test of the api')


