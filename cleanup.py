#!/usr/bin/python

"""A tool to delete crappy tracks from your iTunes library."""

import logging
import os
import os.path

import analysis
import pytunes

LOG_FORMAT = '%(message)s'

logger = logging.getLogger(__name__)


def delete_crappy_singles(songs, albums, min_rating=80, dryrun=True):
    logger.info('Deleting crappy singles...')
    crappy_singles = analysis.find_crappy_single_tracks(songs, albums, min_rating)
    # 10 means 0 stars in iTunes. We consider 0 stars as unrated.
    for track in crappy_singles:
        location = track.location.replace('file://', '')
        logger.info('Deleting ' + location)
        if dryrun:
            print ('rm "%s"' % location).encode('utf-8')
        else:
            os.remove(location)


def delete_crappy_albums(
        albums, min_good_tracks=4, min_rating=80, keep_good_tracks=True,
        dryrun=True):
    logger.info('Deleting crappy albums...')
    crappy_albums = analysis.find_crappy_albums(albums, min_good_tracks, min_rating)
    sorted_crappy_albums = sorted(crappy_albums, key=lambda a: a.artist)
    delete_albums(sorted_crappy_albums, min_rating, keep_good_tracks, dryrun)


def delete_compilations(
        albums, min_rating=80, keep_good_tracks=True, dryrun=True):
    logger.info('Deleting compilations...')
    completely_rated_albums = analysis.find_completely_rated_albums(albums)
    compilations = analysis.find_compilations(completely_rated_albums)
    sorted_compilations = sorted(compilations, key=lambda a: a.artist)
    delete_albums(sorted_compilations, min_rating, keep_good_tracks, dryrun)


def delete_albums(albums, min_rating=80, keep_good_tracks=True, dryrun=True):
    for album in albums:
        source = album.tracks[0].location.replace('file://', '')
        source_dir = os.path.dirname(source)
        if not os.path.exists(source_dir):
            logger.warning('Path does not exist: %s.', source_dir)
            continue
        source_base = os.path.basename(source)
        source_parent = os.path.split(source_dir)[0]

        for track in album.tracks:
            source = track.location.replace('file://', '')
            if track.rating >= min_rating:
                if keep_good_tracks:
                    target_dir = source_parent
                    target_file = '%s - %s.mp3' % (track.artist, track.name)
                    target = os.path.join(target_dir, target_file)
                    if dryrun:
                        logger.info('Moving ' + source)
                        print ('mv "%s" "%s"' % (source, target)) \
                                .encode('utf-8')
                    else:
                        os.rename(source, target)
            else:
                logger.info('Deleting ' + source)
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


def main():
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

    logger.info('Opening iTunes library...')
    lib = pytunes.Library()
    logger.info('Loading all tracks...')
    songs = filter(lambda t: not t.podcast, lib.tracks)
    albums = list(pytunes.Album.group_tracks_into_albums(songs))
    dryrun = True
    min_rating = 80  # 4 stars.
    min_good_tracks = 4
    keep_good_tracks = True
    tolerated_time_difference = 10

    delete_crappy_singles(songs, albums, min_rating, dryrun)
    delete_crappy_albums(
            albums, min_good_tracks, min_rating, keep_good_tracks, dryrun)
    delete_compilations(albums, min_rating, keep_good_tracks, dryrun)


if __name__ == '__main__':
    main()
