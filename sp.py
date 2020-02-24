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

#follwing are sorting functions for create_related_artist_list
def second_tuple_length(artist_tuple):
    return len(artist_tuple[1])

sorting_functions = [second_tuple_length]

def create_related_artist_list(related_artist_dict, sorting_function = sorting_functions[0]):
    related_artist_list = [(artist, related_artists) for artist, related_artists
                           in related_artist_dict.items()]
    related_artist_list.sort(key = sorting_function, reverse=True)  
    return related_artist_list

def create_inverse_related_artist_list(related_dict):
    inverse_dict = {}
    for artist in related_dict:
        inverse_dict[artist] = []
        for key in related_dict:
            for related_artist in related_dict[key]:
                if artist == related_artist:
                    inverse_dict[artist].append(key)
    if not len(inverse_dict) == len(related_dict):
        print('ERROR - Dict length not matched')
    return inverse_dict

def create_groups(related_dict):
    groups = []
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
        count += len(group_list)
    return count

def average_group(group_list):
    count = count_group(group_list)
    groups = len(group_list)
    return int(count/groups)

def max_groups(group_list):
    length_list = [len(group) for group in group_list]
    return max(length_list)

def median_groups(group_list):
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
