#!/usr/bin/python

"""A tool to run stats over your iTunes library.

Can also be used to delete crappy tracks."""

import logging
import os
import os.path

import pytunes

LOG_FORMAT = '%(message)s'

logger = logging.getLogger(__name__)


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


def print_incompletely_rated_albums(albums):
    print 'Incompletely rated albums:'
    incompletely_rated_albums = find_incompletely_rated_albums(albums)
    albums_sorted_by_completeness = sorted(
            incompletely_rated_albums, key=lambda a: a.rating_completeness)
    for album in albums_sorted_by_completeness:
        print unicode(album).encode('utf-8')
    print


def print_best_albums(albums, n=50):
    print '%d best rated albums:' % n
    completely_rated_albums = find_completely_rated_albums(albums)
    albums_sorted_by_rating = sorted(
            completely_rated_albums, key=lambda a: a.avg_rating)
    for album in reversed(albums_sorted_by_rating[-n:]):
        print unicode(album).encode('utf-8')
    print


def print_worst_albums(albums, n=50):
    print '%d worst rated albums:' % n
    completely_rated_albums = find_completely_rated_albums(albums)
    albums_sorted_by_rating = sorted(
            completely_rated_albums, key=lambda a: a.avg_rating)
    for album in albums_sorted_by_rating[:n]:
        print unicode(album).encode('utf-8')
    print


def print_crappy_singles(all_tracks, albums, min_rating=80):
    print 'Crappy singles:'
    crappy_singles = find_crappy_single_tracks(all_tracks, albums, min_rating)
    for track in crappy_singles:
        location = track.location.replace('file://localhost', '')
        print '%s - %s - %0.2f - %s' % (
                track.artist, track.name, track.rating, location)
    print


def delete_crappy_singles(all_tracks, albums, min_rating=80, dryrun=True):
    logger.info('Deleting crappy singles...')
    crappy_singles = find_crappy_single_tracks(all_tracks, albums, min_rating)
    # 10 means 0 stars in iTunes. We consider 0 stars as unrated.
    for track in crappy_singles:
        location = track.location.replace('file://localhost', '')
        logger.info(location)
        if dryrun:
            print 'rm "%s"' % location
        else:
            os.remove(location)


def print_crappy_albums(albums, min_good_tracks=4, min_rating=80):
    print 'Crappy albums:'
    crappy_albums = find_crappy_albums(albums, min_good_tracks, min_rating)
    for album in crappy_albums:
        print unicode(album).encode('utf-8')
    print


def delete_crappy_albums(
        albums, min_good_tracks=4, min_rating=80, keep_good_tracks=True,
        dryrun=True):
    logger.info('Deleting crappy albums...')
    crappy_albums = find_crappy_albums(albums, min_good_tracks, min_rating)
    sorted_crappy_albums = sorted(crappy_albums, key=lambda a: a.artist)
    delete_albums(sorted_crappy_albums, min_rating, keep_good_tracks, dryrun)


def delete_compilations(
        albums, min_rating=80, keep_good_tracks=True, dryrun=True):
    logger.info('Deleting compilations...')
    completely_rated_albums = find_completely_rated_albums(albums)
    compilations = find_compilations(completely_rated_albums)
    sorted_compilations = sorted(compilations, key=lambda a: a.artist)
    delete_albums(sorted_compilations, min_rating, keep_good_tracks, dryrun)


def delete_albums(albums, min_rating=80, keep_good_tracks=True, dryrun=True):
    for album in albums:
        source = album.tracks[0].location.replace('file://localhost', '')
        source_dir = os.path.dirname(source)
        if not os.path.exists(source_dir):
            logger.warning('Path does not exist: %s.', source_dir)
            continue
        source_base = os.path.basename(source)
        source_parent = os.path.split(source_dir)[0]

        for track in album.tracks:
            source = track.location.replace('file://localhost', '')
            logger.info(source)
            if track.rating >= min_rating:
                if keep_good_tracks:
                    target_dir = source_parent
                    target_file = '%s - %s.mp3' % (track.artist, track.name)
                    target = os.path.join(target_dir, target_file)
                    if dryrun:
                        print ('mv "%s" "%s"' % (source, target)) \
                                .encode('utf-8')
                    else:
                        os.rename(source, target)
            else:
                if dryrun:
                    print ('rm "%s"' % source).encode('utf-8')
                else:
                    os.remove(source)
        if dryrun:
            print ('rmdir "%s"' % source_dir).encode('utf-8')
        else:
            try:
                os.rmdir(source_dir)
            except OSError, e:
                logger.error(e)


def print_duplicates(tracks, tolerated_time_difference=10):
    print 'Duplicates:'
    duplicates = find_duplicates(tracks, tolerated_time_difference)
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

    print_incompletely_rated_albums(albums)
    print_best_albums(albums, n)
    print_worst_albums(albums, n)
    print_crappy_singles(all_tracks, albums, min_rating)
    delete_crappy_singles(all_tracks, albums, min_rating, dryrun)
    print_crappy_albums(albums, min_good_tracks, min_rating)
    delete_crappy_albums(
            albums, min_good_tracks, min_rating, keep_good_tracks, dryrun)
    delete_compilations(albums, min_rating, keep_good_tracks, dryrun)
    print_duplicates(all_tracks, tolerated_time_difference)


if __name__ == '__main__':
    main()
