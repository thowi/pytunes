#!/usr/bin/python

"""A tool to run stats over your iTunes library."""

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


def print_crappy_singles(all_tracks, albums, min_rating=80):
    print 'Crappy singles:'
    crappy_singles = analysis.find_crappy_single_tracks(all_tracks, albums, min_rating)
    for track in crappy_singles:
        location = track.location.replace('file://localhost', '')
        print '%s - %s - %0.2f - %s' % (
                track.artist, track.name, track.rating, location)
    print


def print_crappy_albums(albums, min_good_tracks=4, min_rating=80):
    print 'Crappy albums:'
    crappy_albums = analysis.find_crappy_albums(albums, min_good_tracks, min_rating)
    for album in crappy_albums:
        print unicode(album).encode('utf-8')
    print


def print_duplicates(tracks, tolerated_time_difference=10):
    print 'Duplicates:'
    duplicates = analysis.find_duplicates(tracks, tolerated_time_difference)
    sorted_duplicates = sorted(
            duplicates, key=lambda t: '%s-%s' % (t.artist, t.name))
    for track in sorted_duplicates:
        print unicode(track).encode('utf-8')


def main():
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

    logger.info('Opening iTunes library...')
    lib = pytunes.Library()
    logger.info('Loading all tracks...')
    all_tracks = list(lib.tracks)
    albums = list(pytunes.Album.group_tracks_into_albums(all_tracks))
    dryrun = True
    n = 20
    min_rating = 80  # 4 stars.
    min_good_tracks = 4
    keep_good_tracks = True
    tolerated_time_difference = 10

    #print_incompletely_rated_albums(albums)
    #print_best_albums(albums, n)
    #print_worst_albums(albums, n)
    #print_crappy_singles(all_tracks, albums, min_rating)
    #delete_crappy_singles(all_tracks, albums, min_rating, dryrun)
    #print_crappy_albums(albums, min_good_tracks, min_rating)
    #delete_crappy_albums(
    #        albums, min_good_tracks, min_rating, keep_good_tracks, dryrun)
    #delete_compilations(albums, min_rating, keep_good_tracks, dryrun)
    #print_duplicates(all_tracks, tolerated_time_difference)


if __name__ == '__main__':
    main()
