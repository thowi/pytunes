#!/usr/bin/python

"""A tool to run stats over your iTunes library."""

import collections
import logging
import os
import os.path

import analysis
import pytunes

LOG_FORMAT = '%(message)s'

logger = logging.getLogger(__name__)


def print_incompletely_rated_albums(albums):
    print 'Incompletely rated albums:'
    incompletely_rated_albums = analysis.find_incompletely_rated_albums(albums)
    albums_sorted_by_completeness = sorted(
            incompletely_rated_albums, key=lambda a: a.rating_completeness)
    for album in albums_sorted_by_completeness:
        print unicode(album).encode('utf-8')
    print


def print_best_albums(albums, n=50):
    print '%d best rated albums:' % n
    completely_rated_albums = analysis.find_completely_rated_albums(albums)
    albums_sorted_by_rating = sorted(
            completely_rated_albums, key=lambda a: a.avg_rating)
    for album in reversed(albums_sorted_by_rating[-n:]):
        print unicode(album).encode('utf-8')
    print


def print_worst_albums(albums, n=50):
    print '%d worst rated albums:' % n
    completely_rated_albums = analysis.find_completely_rated_albums(albums)
    albums_sorted_by_rating = sorted(
            completely_rated_albums, key=lambda a: a.avg_rating)
    for album in albums_sorted_by_rating[:n]:
        print unicode(album).encode('utf-8')
    print


def print_duplicates(tracks, tolerated_time_difference=10):
    print 'Duplicates:'
    duplicates = analysis.find_duplicates(tracks, tolerated_time_difference)
    sorted_duplicates = sorted(
            duplicates, key=lambda t: '%s-%s' % (t.artist, t.name))
    for track in sorted_duplicates:
        print unicode(track).encode('utf-8')


def print_favorite_bands(songs, n=50):
    print '%d favorite bands (by number of tracks in the library):' % n
    counter = collections.Counter()
    counter.update([t.artist for t in songs])
    for artist, count in counter.most_common(n):
        print '%s - %d' % (unicode(artist).encode('utf-8'), count)
    print


def print_best_bands(songs, min_rating, n=50):
    print '%d best bands (by number of highly rated tracks):' % n
    good_tracks = filter(lambda t: t.rating >= min_rating, songs)
    counter = collections.Counter()
    counter.update([t.artist for t in good_tracks])
    for artist, count in counter.most_common(n):
        print '%s - %d' % (unicode(artist).encode('utf-8'), count)
    print


def main():
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

    logger.info('Opening iTunes library...')
    lib = pytunes.Library()
    logger.info('Loading all tracks...')
    songs = filter(lambda t: not t.podcast, lib.tracks)
    albums = list(pytunes.Album.group_tracks_into_albums(songs))
    albums = filter(lambda a: len(a.tracks) > 7, albums)
    htgt = filter(lambda a: a.album == 'Here Today Gone Tomorrow', albums)[0]
    dryrun = True
    n = 10
    min_rating = 80  # 4 stars.
    min_good_tracks = 4
    keep_good_tracks = True
    tolerated_time_difference = 10

    print_best_albums(albums, n)
    print_best_bands(songs, min_rating, n)
    print_favorite_bands(songs, n)
    print_worst_albums(albums, n)
    print_incompletely_rated_albums(albums)
    print_duplicates(songs, tolerated_time_difference)


if __name__ == '__main__':
    main()
