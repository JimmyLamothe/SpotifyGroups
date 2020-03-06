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

    def get_current_track(self):
        current = self.instance.currently_playing()
        return current

    def get_simple_current(self):
        current = self.get_current_track()
        return sp.simplify_current(current)

    def get_recommendations(self, track_uri):
        return sp.get_recommendations(self.instance, track_uri) 

    def get_current_recommendations(self, exclude_current_artist = True):
        current = self.get_simple_current()
        track_uri = current['uri']
        artist_name = current['artist_name']
        recs = self.get_recommendations(track_uri)
        if exclude_current_artist:
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

    def play_next_album(self, followed = False, new = False): #Mutually exclusive
        base_recs = self.get_current_recommendations()
        recs = self.process_recs(base_recs, followed = followed, new = new)
        next_artist = sp.get_random_artist(recs)
        next_album = sp.get_random_album(self.instance, next_artist['artist_uri'])
        print('Now playing: ' + sp.get_name(next_album) +
              ' by ' + sp.get_artist_name(next_album))
        self.instance.start_playback(context_uri = sp.get_uri(next_album))

    def play_current_album(self):
        current_track = self.get_simple_current()
        album_uri = current_track['album_uri']
        album_name = current_track['album_name']
        artist_name = current_track['artist_name']
        print('Now playing: ' + album_name +
              ' by ' + artist_name)
        self.instance.start_playback(context_uri = album_uri)

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
