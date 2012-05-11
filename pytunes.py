#!/usr/bin/python

"""A pythonic interface to the iTunes library."""

import getpass
import os.path
import plistlib
import urllib2


class Library(object):
    """An iTunes library.
    
    The items are loaded lazily and/or cached where possible.
    """
    
    _lib = None
    _playlists_cache = None
    _tracks_by_id_cache = {}

    def __init__(self, path=None):
        """Creates a new Library.

        @param path: The path to the iTunes library. Optional. Defaults to
                /Users/$USER/Music/iTunes/iTunes Music Library.xml.
        @type path: str
        """
        self._path = path
    
    def _open(self):
        path = self._path
        # TODO: Add path auto-detection for other OSes.
        if path is None:
            user = getpass.getuser()
            path = '/Users/%s/Music/iTunes/iTunes Music Library.xml' % user
            if not os.path.exists(path):
                path = '/Users/%s/Music/iTunes/iTunes Library.xml' % user
        self._lib = plistlib.readPlist(path)
    
    def _ensure_opened(self):
        if self._lib is None:
            self._open()
    
    @property
    def playlists(self):
        self._ensure_opened()
        if self._playlists_cache is None:
            self._playlists_cache = []
            tracks_by_id = {}
            for track in self.tracks:
                tracks_by_id[track.id] = track
            for playlist_item in self._lib['Playlists']:
                playlist = Playlist.from_plist_item(playlist_item, tracks_by_id)
                self._playlists_cache.append(playlist)
        return self._playlists_cache
    
    @property
    def tracks(self):
        self._ensure_opened()
        for track_id, track_item in self._lib['Tracks'].iteritems():
            track = self._tracks_by_id_cache.get(track_id)
            if not track:
                track = Track.from_plist_item(track_item)
                self._tracks_by_id_cache[track_id] = track
            yield track
    
    def __str__(self):
        return 'Library(%s)' % self._path


class Playlist(object):
    """A playlist."""
    
    all_items = None
    distinguished_kind = None
    id = None
    master = None
    name = None
    persistent_id = None
    smart_criteria = None
    smart_info = None
    visible = None
    _all_tracks = {}
    _item_ids = []
    
    def __init__(self, all_tracks):
        """Creates a new playlist.
        
        @param all_tracks: All tracks in the library, keyed by ID. Needed to
                reference the tracks from the playlist.
        @type all_tracks: {str, Track}
        """
        self._all_tracks = all_tracks
    
    @staticmethod
    def from_plist_item(item, all_tracks):
        playlist = Playlist(all_tracks)
        playlist.all_items = item.get('All Items')
        playlist.distinguished_kind = item.get('Distinguished Kind')
        playlist.id = item.get('Playlist ID')
        playlist.master = item.get('Master')
        playlist.name = item.get('Name')
        playlist.persistent_id = item.get('Persistent ID')
        playlist.smart_criteria = item.get('Smart Criteria')
        playlist.smart_info = item.get('Smart Info')
        playlist.visible = item.get('Visible')
        items = item.get('Playlist Items', [])
        playlist._item_ids = map(lambda i: i['Track ID'], items)
        return playlist
    
    @property
    def items(self):
        for item_id in self._item_ids:
            yield self._all_tracks[item_id]
    
    def __str__(self):
        return 'Playlist(id=%s)' % self.id


class Track(object):
    """A track."""
    
    album = None
    album_artist = None
    album_rating = None
    album_rating_computed = None
    artist = None
    artwork_count = None
    bit_rate = None
    date_added = None
    date_modified = None
    file_folder_count = None
    genre = None
    id = None
    kind = None
    library_folder_count = None
    location = None
    name = None
    number = None
    persistent_id = None
    play_count = None
    play_date = None
    play_date_utc = None
    rating = None
    sample_rate = None
    size = None
    skip_count = None
    total_time = None
    type = None
    year = None
    
    @staticmethod
    def from_plist_item(item):
        track = Track()
        track.album = item.get('Album')
        track.album_artist = item.get('Album Artist')
        track.album_rating = item.get('Album Rating')
        track.album_rating_computed = item.get('Album Rating Computed')
        track.artist = item.get('Artist')
        track.artwork_count = item.get('Artwork Count')
        track.bit_rate = item.get('Bit Rate')
        track.date_added = item.get('Date Added')
        track.date_modified = item.get('Date Modified')
        track.file_folder_count = item.get('File Folder Count')
        track.genre = item.get('Genre')
        track.id = item.get('Track ID')
        track.kind = item.get('Kind')
        track.library_folder_count = item.get('Library Folder Count')
        track.location = item.get('Location')
        if track.location:
            track.location = urllib2.unquote(track.location).decode('utf-8')
        track.name = item.get('Name')
        track.number = item.get('Track Number')
        track.persistent_id = item.get('Persistent ID')
        track.play_count = item.get('Play Count')
        track.play_date = item.get('Play Date')
        track.play_date_utc = item.get('Play Date UTC')
        track.rating = item.get('Rating')
        track.sample_rate = item.get('Sample Rate')
        track.size = item.get('Size')
        track.skip_count = item.get('Skip Count')
        track.total_time = item.get('Total Time')
        track.type = item.get('Track Type')
        track.year = item.get('Year')
        return track
        
    @property
    def items(self):
        for item_id in self._item_ids:
            yield self._all_tracks[item_id]
    
    def __str__(self):
        return '''Track(id='%s', artist='%s', name='%s')''' % (
                self.id, self.artist, self.name)
