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

    def __unicode__(self):
        return 'Library(%s)' % self._path

    def __str__(self):
        return unicode(self).encode('utf-8')


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

    def __unicode__(self):
        return 'Playlist(id=%s)' % self.id

    def __str__(self):
        return unicode(self).encode('utf-8')


class Track(object):
    """A track."""

    album = None
    album_artist = None
    album_rating = None
    album_rating_computed = None
    artist = None
    artwork_count = None
    bit_rate = None
    composer = None
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
    podcast = None
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
        track.composer = item.get('Composer')
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
        track.podcast = item.get('Podcast')
        track.rating = item.get('Rating')
        track.sample_rate = item.get('Sample Rate')
        track.size = item.get('Size')
        track.skip_count = item.get('Skip Count')
        track.total_time = item.get('Total Time')
        track.type = item.get('Track Type')
        track.year = item.get('Year')
        return track


    def __unicode__(self):
        return '''Track(id='%s', artist='%s', name='%s')''' % (
                self.id, self.artist, self.name)

    def __str__(self):
        return unicode(self).encode('utf-8')


class Album(object):
    """An album.

    Note that the iTunes library doesn't have a clear concept of an album.
    It's just tracks, that can be grouped into albums.

    So this class is also just a collection of tracks, and all properties are
    derived from the tracks in this album.

    The properties are calculated lazily and then cached.

    You can group tracks into Albums using Album.group_tracks_into_albums.
    """

    _avg_rating_cache = None
    _is_compilation_cache = None
    _rating_completeness_cache = None

    def __init__(self, artist, year, album, tracks=None):
        self.artist = artist
        self.year = year
        self.album = album
        if tracks:
            self.tracks = tracks
        else:
            self.tracks = []

    @property
    def avg_rating(self):
        if self._avg_rating_cache is None:
            rated_tracks = filter(lambda t: t.rating, self.tracks)
            if len(rated_tracks):
                self._avg_rating_cache = (
                        float(sum(t.rating for t in rated_tracks))
                        / len(rated_tracks))
            else:
                self._avg_rating_cache = 0.0
        return self._avg_rating_cache

    @property
    def rating_completeness(self):
        if self._rating_completeness_cache is None:
            # 10 means 0 stars in iTunes. We consider 0 stars as unrated.
            rated_tracks = filter(lambda t: t.rating > 10, self.tracks)
            self._rating_completeness_cache = \
                    1.0 * len(rated_tracks) / len(self.tracks)
        return self._rating_completeness_cache

    @property
    def is_compilation(self):
        if self._is_compilation_cache is None:
            unique_artists = set(map(lambda t: t.artist, self.tracks))
            self._is_compilation_cache = len(unique_artists) > 1
        return self._is_compilation_cache

    @staticmethod
    def group_tracks_into_albums(tracks):
        """Groups some tracks into Albums.

        A track is considered part of an Album when it has a track number and
        year, and when the album artist (or artist if there is no album artist),
        year, album, and the files are in the same directory, with no other
        tracks in the same directory.

        @return: Yields the grouped albums.
        @rtype: generator(Album)
        """
        albums_by_key = {}
        albums_by_directory = {}

        # Identify unique, potential albums.
        for track in tracks:
            if track.album_artist:
                artist = track.album_artist
            else:
                artist = track.artist

            if (not artist or not track.number or not track.year or
                not track.album):
                continue

            location = track.location.replace('file://', '')
            directory = os.path.split(location)[0]

            album_key = '%s-%s-%s-%s' % (
                    artist, track.year, track.album, directory)

            album = albums_by_key.get(album_key)
            if not album:
                album = Album(artist, track.year, track.album)
                albums_by_key[album_key] = album
                albums_by_directory.setdefault(directory, [])
                albums_by_directory[directory].append(album)

            album.tracks.append(track)

        # Only consider those albums where there are no other tracks in the same
        # directory. Otherwise single tracks might be treated as albums.
        for directory, albums in albums_by_directory.iteritems():
            if len(albums) == 1:
                yield albums[0]

    def __unicode__(self):
        return '%s - %s - %s - Average rating: %0.2f - Rating completeness: %0.2f' % (
                self.artist, self.year, self.album, self.avg_rating,
                self.rating_completeness)

    def __str__(self):
        return unicode(self).encode('utf-8')
