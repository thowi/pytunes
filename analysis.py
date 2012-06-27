#!/usr/bin/python

"""A Python library to analyze your iTunes library.

All functions expect data from the pytunes library.
"""


def find_completely_rated_albums(albums):
    return filter(lambda a: a.rating_completeness == 1, albums)


def find_incompletely_rated_albums(albums):
    return filter(lambda a: a.rating_completeness < 1, albums)


def find_compilations(albums):
    return filter(lambda a: a.is_compilation, albums)


def find_single_tracks(all_tracks, albums):
    tracks_in_albums = set()
    for album in albums:
        tracks_in_albums.update(set(album.tracks))
    single_tracks = set(all_tracks) - tracks_in_albums
    return single_tracks


def find_crappy_single_tracks(all_tracks, albums, min_rating=80):
    single_tracks = find_single_tracks(all_tracks, albums)
    # 10 means 0 stars in iTunes. We consider 0 stars as unrated.
    return filter(
            lambda t: t.rating is not None and 10 < t.rating < min_rating,
            single_tracks)


def find_crappy_albums(albums, min_good_tracks=4, min_rating=80):
    completely_rated_albums = find_completely_rated_albums(albums)
    for album in completely_rated_albums:
        good_tracks = filter(lambda t: t.rating >= min_rating, album.tracks)
        if len(good_tracks) < min_good_tracks < len(album.tracks):
            yield album


def find_duplicates(tracks, tolerated_time_difference=10):
    grouped_tracks = {}
    for track in tracks:
        key = '%s-%s' % (track.artist, track.name)
        grouped_tracks.setdefault(key, [])
        grouped_tracks[key].append(track)
    duplicates = set()
    for group in grouped_tracks.itervalues():
        tracks_sorted_by_time = sorted(group, key=lambda t: t.total_time)
        last_track = None
        for track in tracks_sorted_by_time:
            if last_track is not None:
                time_difference = abs(last_track.total_time - track.total_time)
                if time_difference <= tolerated_time_difference:
                    duplicates.add(last_track)
                    duplicates.add(track)
            last_track = track
    return duplicates
