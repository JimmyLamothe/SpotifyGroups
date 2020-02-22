import os, sys, json 
import spotipy
import spotipy.util as util
import pprint as pp

def set_environment(filepath):
    environment_dict = None
    with open(filepath, 'r') as json_file:
        environment_dict = json.load(json_file)
    for key in environment_dict:
        os.environ[key] = environment_dict[key]
    print('Configuration Succesful')

set_environment('environment.json')

def get_token(scope = None, user = None):
    print('getting token')
    if not scope:
        scope = input('Scope:\n')
    if not user:
        user = input('User:\n')
    token = util.prompt_for_user_token(user, scope)
    return token

def get_instance(token):
    print('getting instance')
    instance = spotipy.Spotify(auth=token)
    return instance

def get_followed_items(page):
    print('getting followed items')
    items = page['artists']['items']
    return items

def get_followed_page(sp = None, after=None):
    print('getting followed page')
    if not sp:
        return ValueError('No spotify instance')
    page = sp.current_user_followed_artists(limit=50, after=after)
    return page

def get_followed_after(page):
    print('getting followed after')
    after = page['artists']['cursors']['after']
    return after

def get_artist_list(sp = None):
    print('getting artist list')
    if not sp:
        token = get_token(scope = 'user-follow-read')
        sp = get_instance(token)
    artist_list = []
    print('getting first page')
    first_page = get_followed_page(sp = sp)
    after = get_followed_after(first_page)
    artist_list.extend(get_followed_items(first_page))
    while after:
        next_page = get_followed_page(sp = sp, after = after)
        artist_list.extend(get_followed_items(next_page))
        after = get_followed_after(next_page)
    return artist_list

def format_artist_list(artist_list):
    artist_dict = {}
    for artist in artist_list:
        name = artist['name']
        uri = artist['uri']
        artist_dict[name] = uri
    return artist_dict

def get_related_artist_list(related_artist_dict):
    print('getting related artist list')
    artist_list = []
    for artist in related_artist_dict['artists']:
        name = artist['name']
        artist_list.append(name)
    return artist_list

def get_related_artists(uri, sp):
    artist_dict = sp.artist_related_artists(uri)
    artist_list = get_related_artist_list(artist_dict)
    return artist_list

def simplify_related_artist_list(related_artist_list, followed_artists_list):
    simple_list = []
    for artist in related_artist_list:
        if artist in followed_artists_list:
            simple_list.append(artist)
    return simple_list

def create_related_artist_dict(artist_dict, sp):
    related_artist_dict = {}
    artist_list = [key for key in artist_dict]
    for artist in artist_dict:
        print('Finding related artists for ' + artist)
        related_list = get_related_artists(artist_dict[artist], sp = sp)
        short_list = simplify_related_artist_list(related_list, artist_list)
        related_artist_dict[artist] = short_list
    return related_artist_dict

def create_groups(related_artist_dict):
    pass
