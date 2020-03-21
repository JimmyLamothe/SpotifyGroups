import time, multiprocessing
import sp

class Player:
    def __init__(self):
        scope = 'user-modify-playback-state user-read-currently-playing '
        scope += 'user-follow-read user-follow-modify'
        token = sp.get_token(scope)
        self.instance = sp.get_instance(token)
        followed_artist_dicts = sp.get_full_artist_dicts(instance = self.instance)
        self.simple_artist_dict = sp.get_simple_artist_dict(followed_artist_dicts)
        self.artist_list = sp.get_followed_artist_list(self.simple_artist_dict)
        self.play_followed = False
        self.play_new = False
        self.exclude_current = True
        self.process = None

    def play_followed(self):
        self.play_followed = True
        self.play_new = False

    def play_new(self):
        self.play_new = True
        self.play_followed = False

    def play_all(self):
        self.play_followed = False
        self.play_new = False

    def include_current(self):
        self.exclude_current = False

    def exclude_current(self):
        self.exclude_current = True

    def get_current_track(self):
        current = self.instance.currently_playing()
        return current

    def get_simple_current(self):
        current = self.get_current_track()
        return sp.simplify_current(current)

    def get_current_album(self):
        current = self.get_current_track()
        album_uri = current['item']['album']['uri']
        album = sp.get_album(self.instance, album_uri)
        return album

    def get_recommendations(self, track_uri):
        return sp.get_recommendations(self.instance, track_uri) 

    def get_current_recommendations(self):
        current = self.get_simple_current()
        track_uri = current['uri']
        artist_name = current['artist_name']
        recs = self.get_recommendations(track_uri)
        if self.exclude_current:
            recs = sp.exclude_artist(recs, artist_name)
        return recs

    def process_recs(self, recs, followed = False, new = False):
        if followed == True:
            followed_recs = sp.get_followed_rec_list(recs, self.artist_list)
            if followed_recs:
                recs = followed_recs
        elif new == True:
            new_recs = sp.get_new_rec_list(recs, self.artist_list)
            if new_recs:
                recs = new_recs
        return recs

    def queue_next_album(self, track_list, index):
        album_time = sp.get_total_track_time(track_list) / 1000
        print('Album time: ' + sp.seconds_to_minutes(album_time))
        def play_track(track_dict):
            print('Current track: ' + track_dict['name'])
            track_time = track_dict['duration_ms'] / 1000
            print('Track time: ' + sp.seconds_to_minutes(track_time))
            time.sleep(track_time)
        for track_dict in track_list[index:]:
            play_track(track_dict)
        time.sleep(1)
        self.play_next_album()
        #return - Test if return makes a difference to running processes

    def set_queue(self, track_list, index=0):
        self.process = multiprocessing.Process(target = self.queue_next_album,
                                               args = (track_list, index))
        self.process.start()

    def stop_queue(self):
        print(multiprocessing.active_children())
        for process in multiprocessing.active_children():
            process.terminate()

    def play_next_album(self):
        print('Previous number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        self.stop_queue()
        print('New number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        base_recs = self.get_current_recommendations()
        recs = self.process_recs(base_recs, followed = self.play_followed, new = self.play_new)
        next_artist = sp.get_random_artist(recs)
        next_album = sp.get_random_album(self.instance, next_artist['artist_uri'])
        print('Now playing: ' + sp.get_name(next_album) +
              ' by ' + sp.get_artist_name(next_album))
        album_uri = sp.get_uri(next_album)
        album_time = sp.get_album_time(self.instance, album_uri)
        album = sp.get_album(self.instance, album_uri)
        track_list = sp.get_track_list(album)
        self.instance.start_playback(context_uri = album_uri)
        self.set_queue(track_list)
        
    def play_current_album(self):
        print('Previous number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        self.stop_queue()
        print('New number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        current_track = self.get_simple_current()
        album_uri = current_track['album_uri']
        album_name = current_track['album_name']
        artist_name = current_track['artist_name']
        print('Now playing: ' + album_name +
              ' by ' + artist_name)
        album_time = sp.get_album_time(self.instance, album_uri)
        album = sp.get_album(self.instance, album_uri)
        track_list = sp.get_track_list(album)
        self.instance.start_playback(context_uri = album_uri)
        self.set_queue(track_list)

    def play_next_track(self):
        print('Previous number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        self.stop_queue()
        print('New number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        current_track = self.get_current_track()
        album = self.get_current_album()
        current_track_number = current_track['item']['track_number']
        next_index = current_track_number
        next_track_name = album['tracks']['items'][next_index]['name']
        album_name = album['name']
        album_uri = album['uri']
        artist_name = album['artists'][0]['name']
        print('Now playing: ' + album_name +
              ' by ' + artist_name)
        print('Current track: ' + next_track_name)    
        album_time = sp.get_album_time(self.instance, album_uri)
        album = sp.get_album(self.instance, album_uri)
        track_list = sp.get_track_list(album)
        self.instance.start_playback(context_uri = album_uri, offset = {"position":next_index})
        self.set_queue(track_list, index = next_index - 1)

    def play_previous_track(self):
        print('Previous number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        self.stop_queue()
        print('New number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        current_track = self.get_current_track()
        album = self.get_current_album()
        current_track_number = current_track['item']['track_number']
        next_index = max(0, current_track_number - 2)
        next_track_name = album['tracks']['items'][next_index]['name']
        album_name = album['name']
        album_uri = album['uri']
        artist_name = album['artists'][0]['name']
        print('Now playing: ' + album_name +
              ' by ' + artist_name)
        print('Current track: ' + next_track_name)    
        album_time = sp.get_album_time(self.instance, album_uri)
        album = sp.get_album(self.instance, album_uri)
        track_list = sp.get_track_list(album)
        self.instance.start_playback(context_uri = album_uri, offset = {"position":next_index})
        self.set_queue(track_list, index = next_index - 1)

    def show_current_track(self):
        print('Previous number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        self.stop_queue()
        print('New number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        current_track = self.get_simple_current()
        album_uri = current_track['album_uri']
        album_name = current_track['album_name']
        artist_name = current_track['artist_name']
        print('Now playing: ' + album_name +
              ' by ' + artist_name)
        print('Current track: ' + current_track['name'])    

    def play_random_album(self):
        print('Previous number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        self.stop_queue()
        print('New number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        artist_uri = sp.get_random_followed_artist(self.simple_artist_dict)
        next_album = sp.get_random_album(self.instance, artist_uri)
        print('Now playing: ' + sp.get_name(next_album) +
              ' by ' + sp.get_artist_name(next_album))
        album_uri = sp.get_uri(next_album)
        album_time = sp.get_album_time(self.instance, album_uri)
        album = sp.get_album(self.instance, album_uri)
        track_list = sp.get_track_list(album)
        self.instance.start_playback(context_uri = album_uri)
        self.set_queue(track_list)

    def stop(self):
        print('Previous number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        self.stop_queue()
        print('New number of running processes: ' + 
              str(len(multiprocessing.active_children())))
        self.instance.pause_playback()

    def follow(self):
        current_track = self.get_simple_current()
        artist_name = current_track['artist_name']
        artist_uri = current_track['artist_uri']
        artist_id = sp.get_id(artist_uri)
        print('Now following ' + artist_name + '.')
        self.instance.user_follow_artists(ids=[artist_id])
    
    def unfollow(self):
        current_track = self.get_simple_current()
        artist_name = current_track['artist_name']
        artist_uri = current_track['artist_uri']
        artist_id = sp.get_id(artist_uri)
        print('Stopped following ' + artist_name + '.')
        self.instance.user_unfollow_artists(ids=[artist_id])

    def __repr__(self):
        return str(self.__dict__)
