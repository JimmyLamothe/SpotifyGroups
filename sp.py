import os, sys, json, random
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

def get_followed_page(instance = None, after=None):
    print('getting followed pagee')
    if not instance:
        return ValueError('No spotify instance')
    page = instance.current_user_followed_artists(limit=50, after=after)
    return page

def get_followed_after(page):
    print('getting followed after')
    after = page['artists']['cursors']['after']
    return after

def get_full_artist_dicts(instance = None):
    print('getting list of full artist dicts')
    if not instance:
        token = get_token(scope = 'user-follow-read')
        instance = get_instance(token)
    artist_dict_list = []
    print('getting first page')
    first_page = get_followed_page(instance = instance)
    after = get_followed_after(first_page)
    artist_dict_list.extend(get_followed_items(first_page))
    while after:
        next_page = get_followed_page(instance = instance, after = after)
        artist_dict_list.extend(get_followed_items(next_page))
        after = get_followed_after(next_page)
    return artist_dict_list

def simplify_artist(artist_dict, genres = False):
    simple_dict = {}
    name = artist_dict['name']
    simple_dict[name] = {'uri' : artist_dict['uri']}
    if genres:
        simple_dict[name]['genres'] = artist_dict['genres']
    return simple_dict

def simplify_album(album_dict):
    simple_dict = {}
    name = album_dict['name']
    uri = album_dict['uri']
    artist_name = album_dict['artists'][0]['name']
    artist_uri = album_dict['artists'][0]['uri']
    type = album_dict['album_type']
    simple_dict[name] = {'uri' : uri,
                         'artist_name' : artist_name,
                         'artist_uri' : artist_uri,
                         'type' : type}
    return simple_dict

def simplify_track(track_dict):
    simple_dict = {}
    name = track_dict['name']
    uri = track_dict['uri']
    artist_name = track_dict['artists'][0]['name']
    artist_uri = track_dict['artists'][0]['uri']
    album_name = track_dict['album']['name']
    album_uri = track_dict['album']['uri']
    album_type = track_dict['album']['album_type']
    simple_dict[name] = {'uri' : uri,
                         'artist_name' : artist_name,
                         'artist_uri' : artist_uri,
                         'album_name' : album_name,
                         'album_uri' : album_uri,
                         'album_type' : album_type}
    return simple_dict
    
def simplify_current(current_dict):
    track = current_dict['item']
    uri = track['uri']
    name = track['name']
    artist = track['artists'][0]
    artist_name = artist['name']
    artist_uri = artist['uri']
    album = track['album']
    album_name = album['name']
    album_uri = album['uri']
    return {'name' : name,
            'uri' : uri,
            'artist_name': artist_name,
            'artist_uri' : artist_uri,
            'album_name' : album_name,
            'album_uri' : album_uri}

def get_simple_artist_dict(artist_dict_list, genres = False):
    simple_artist_dict = {}
    for artist in artist_dict_list:
        simple_artist_dict.update(simplify_artist(artist, genres = genres))
    return simple_artist_dict

def get_followed_artist_list(simple_artist_dict):
    artist_list = []
    for artist_name in simple_artist_dict:
        artist_list.append(artist_name)
    return artist_list

def get_recommendations(instance, track_uri, limit = 100):
    recs = instance.recommendations(seed_tracks=[track_uri], limit = limit)
    simple_recs = [simplify_track(track) for track in recs['tracks']]
    return simple_recs

def exclude_artist(simple_recs, artist_name):
    other_recs = [rec for rec in simple_recs
                  if not rec[list(rec.keys())[0]]['artist_name'] == artist_name]
    return other_recs

def get_followed_rec_list(rec_list, followed_artist_list):
    followed_rec_list = [rec for rec in rec_list
                         if rec[list(rec.keys())[0]]['artist_name'] in followed_artist_list]
    return followed_rec_list

def get_new_rec_list(rec_list, followed_artist_list):
    new_rec_list = [rec for rec in rec_list
                         if not rec[list(rec.keys())[0]]['artist_name'] in followed_artist_list]
    return new_rec_list

def get_random_artist(rec_list):
    selection = random.choice(rec_list)
    artist = selection[list(selection.keys())[0]]
    artist_uri = artist['artist_uri']
    artist_name = artist['artist_name']
    new_dict = {'artist_uri' : artist_uri,
                'artist_name' : artist_name}
    return new_dict

def get_random_album(instance, artist_uri):
    albums = instance.artist_albums(artist_uri, limit=50)
    selection = random.choice(albums['items'])
    return simplify_album(selection)

def get_uri(single_dict):
    uri = single_dict[list(single_dict.keys())[0]]['uri']
    return uri

def get_name(single_dict):
    name = list(single_dict.keys())[0]
    return name

def get_artist_name(single_dict):
    artist_name = single_dict[list(single_dict.keys())[0]]['artist_name']
    return artist_name

def get_id(uri):
    return uri[uri.rindex(':')+1:]

def get_track_time(track_dict):
    return track_dict['duration_ms']

def get_total_track_time(track_list):
    total_track_time = 0
    for track in track_list:
        track_time = int(get_track_time(track))
        total_track_time += track_time
    return total_track_time

def get_album_time(instance, album_uri):
    album = instance.album(album_uri)
    album_ms = get_total_track_time(album['tracks']['items'])
    album_secs = album_ms/1000
    return album_secs

def seconds_to_minutes(secs):
    minutes = int(secs/60)
    seconds = int(secs)%60
    return str(minutes) + 'm' + str(seconds) + 's'

def get_album_from_track(track_dict):
    return track_dict['item']['album']['uri']



























def get_related_artists(uri, instance):
    print('getting related artist list')
    artist_dict = instance.artist_related_artists(uri)
    simple_artist_dict = get_simple_artist_dict(artist_dict['artists'])
    print('Continue')
    related_artist_list = []
    for key in simple_artist_dict:
        related_artist_list.append(key)
    return related_artist_list

def simplify_related_artist_list(related_artist_list, followed_artists_list):
    simple_list = []
    for artist in related_artist_list:
        if artist in followed_artists_list:
            simple_list.append(artist)
    return simple_list

def create_related_artist_dict(simple_artist_dict, instance):
    related_artist_dict = {}
    artist_list = [key for key in simple_artist_dict]
    for artist in simple_artist_dict:
        print('Finding related artists for ' + artist)
        related_list = get_related_artists(simple_artist_dict[artist]['uri'], instance = instance)
        print('related list : ', related_list)
        short_list = simplify_related_artist_list(related_list, artist_list)
        related_artist_dict[artist] = short_list
    return related_artist_dict

#follwing are sorting functions for create_related_artist_list
def second_tuple_length(artist_tuple):
    return len(artist_tuple[1])

sorting_functions = [second_tuple_length]

def create_related_artist_list(related_artist_dict, sorting_function = sorting_functions[0]):
    related_artist_list = [(artist, related_artists) for artist, related_artists
                           in related_artist_dict.items()]
    related_artist_list.sort(key = sorting_function, reverse=True)  
    return related_artist_list

def create_inverse_related_artist_list(related_dict, sorting_function = sorting_functions[0]):
    inverse_dict = {}
    for artist in related_dict:
        inverse_dict[artist] = []
        for key in related_dict:
            print(key)
            print(related_dict[key])
            for related_artist in related_dict[key]:
                if artist == related_artist:
                    inverse_dict[artist].append(key)
    if not len(inverse_dict) == len(related_dict):
        print('ERROR - Dict length not matched')
    inverse_artist_list = [(artist, related_artists) for artist, related_artists
                           in inverse_dict.items()]
    inverse_artist_list.sort(key = sorting_function, reverse=True)
    return inverse_artist_list

def create_groups(related_dict, inverse = False):
    groups = []
    if inverse:
        related_list = create_inverse_related_artist_list(related_dict)
    else:
        related_list = create_related_artist_list(related_dict)
    reference_dict = related_dict.copy()
    for tuple in related_list:
        artist = tuple[0]
        artist_list = tuple[1]
        print('Creating group for: ' + artist)
        print('Following artists are related: ' + str(artist_list))
        if artist in reference_dict:
            new_group = [artist]
            #reference_dict.pop(artist)
            for artist in artist_list:
                if artist in reference_dict:
                    new_group.append(artist)
                    #reference_dict.pop(artist)
            print('Created following group: ' + str(new_group))
            groups.append(new_group)
    return groups

def count_group(group_list):
    count = 0
    for group in group_list:
        count += len(group)
    return count

def average_group(group_list):
    count = count_group(group_list)
    groups = len(group_list)
    return int(count/groups)

def max_group(group_list):
    length_list = [len(group) for group in group_list]
    return max(length_list)

def median_group(group_list):
    length_list = [len(group) for group in group_list]
    median_index = int(len(group_list)/2)
    return length_list[median_index]

def match_percentage(group_list_1, group_list_2):
    matches = 0
    for group in group_list_1:
        if group in group_list_2:
            matches += 1
    match_percentage = int(matches / len(group_list_1) * 100)
    return match_percentage

def remove_singletons(group_list):
    new_list = []
    for group in group_list:
        if len(group) > 1:
            new_list.append(group)
    return new_list

def remove_multiples(group_list):
    new_list = []
    for group in group_list:
        if len(group) == 1:
            new_list.append(group)
    return new_list

def remove_group(match_group, group_list):
    new_list = [group for group in group_list if not group == match_group]
    return new_list

def combine_groups(match_group, group_list, minimum_percentage):
    new_list = []
    max = 0
    max_index = -1
    index = 0
    for target_group in group_list:
        percentage = match_percentage(match_group, target_group)
        if percentage > max and percentage < 100:
            max = percentage
            max_index = index
        index += 1   
    if max > minimum_percentage:
        group_list[max_index].extend(match_group)
        return group_list
    else:
        return False

#Test, doesn't work great
def combine_all_groups(group_list, minimum_percentage):
    working_copy = [group for group in group_list]
    iterations = len(group_list)
    count = 0
    fail_list = []
    temp_list = [group for group in group_list]
    while count < iterations and working_copy:
        match_group = working_copy.pop()
        new_group_list = combine_groups(match_group, temp_list, minimum_percentage)
        if new_group_list:
            temp_list = new_group_list
        else:
            print('Failed to match ' + str(match_group))
            temp_list = remove_group(match_group, working_copy)
            fail_list.append(match_group)
        count += 1
        print(count)
        print(len(group_list))
        temp_list = [list(set(group)) for group in temp_list]
    print('temp list: ' + str(temp_list))
    print('fail list: ' + str(fail_list))
    combined_list = [group for group in temp_list]
    combined_list.extend(fail_list)
    print('\n\n\n\n\n\n\n\n\n')
    print('combined list: ' + str(combined_list))
    return combined_list

def get_sorted_genre_list(simple_artist_dict):
    genre_list = []
    count_list = []
    for artist in simple_artist_dict:
        for genre in simple_artist_dict[artist]['genres']:
            if genre in genre_list:
                index = genre_list.index(genre)
                count_list[index] += 1
            else:
                genre_list.append(genre)
                count_list.append(1)
    tuple_list = list(zip(genre_list, count_list))
    tuple_list.sort(key = lambda x : x[1], reverse = True)
    sorted_genre_list = [item[0] for item in tuple_list]
    return sorted_genre_list
                          
def create_groups_by_genre(simple_artist_dict):
    genre_groups = {}
    genre_list = get_sorted_genre_list(simple_artist_dict)
    for artist in simple_artist_dict:
        for genre in genre_list:
            if genre in simple_artist_dict[artist]['genres']:
                if not genre in genre_groups:
                    genre_groups[genre] = []
                genre_groups[genre].append(artist)
                break
    return genre_groups
                
