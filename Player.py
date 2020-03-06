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

    def queue_next_album(self, track_list):
        album_time = sp.get_total_track_time(track_list) / 1000
        print('Album time: ' + sp.seconds_to_minutes(album_time))
        def play_track(track_dict):
            print('Current track: ' + track_dict['name'])
            track_time = track_dict['duration_ms'] / 1000
            print('Track time: ' + sp.seconds_to_minutes(track_time))
            time.sleep(track_time)
        for track_dict in track_list:
            play_track(track_dict)
        play_next_album()

    def set_queue(self, track_list):
        self.process = multiprocessing.Process(target = self.queue_next_album,
                                               args = (track_list,))
        self.process.start()

    def stop_queue(self):
        if self.process:
            self.process.terminate()

    def play_next_album(self):
        self.stop_queue()
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
        self.stop_queue()
        current_track = self.get_simple_current()
        album_uri = current_track['album_uri']
        album_name = current_track['album_name']
        artist_name = current_track['artist_name']
        print('Now playing: ' + album_name +
              ' by ' + artist_name)
        album_time = sp.get_album_time(self.instance, album_uri)
        album = sp.get_album(album_uri)
        track_list = sp.get_track_list(album)
        self.instance.start_playback(context_uri = album_uri)
        self.set_queue(track_list)

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
