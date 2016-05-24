#!/usr/bin/python

"""A tool to export and diff Moody tags from your iTunes library.

http://www.crayonroom.com/moody.php
"""

import getopt
import logging
import re
import sys

import simplejson

import pytunes

LOG_FORMAT = '%(message)s'
MOODY_PATTERN = re.compile(r'Moody([A-D][1-4])')

logger = logging.getLogger(__name__)


class Usage(Exception):
    """Usage: moody.py
    [-h|--help]   This screen.
    [-e|--export] Print the Moody tags as JSON to STDOUT.
    [-d|--diff]   Loads the Moody tags as JSON from STDIN and prints out differences.
    """
    def __init__(self, msg=''):
        self.msg = msg
    
    def __str__(self):
        return '\n'.join((self.__doc__, str(self.msg)))


def _parse_args(argv):
    export = False
    diff = False
    
    options = 'hed'
    options_long = ['help', 'export=', 'diff=']
    try:
        opts, args = getopt.getopt(argv[1:], options, options_long)
    except getopt.error, msg:
        raise Usage(msg)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print Usage()
            return 0
        if opt in ('-e', '--export'):
            export = True
        if opt in ('-d', '--diff'):
            diff = True

    if not export and not diff:
        raise Usage('Must specify an operation.')
    if export and diff:
        raise Usage('Cannot do export and diff at the same time.')
    
    return export, diff


def _get_mood(track):
	if not track.composer:
		return None
	m = MOODY_PATTERN.match(track.composer)
	if not m:
		return None
	return m.group(1)


def get_moody_tags(tracks):
	mood_by_track = {}
	for track in tracks:
		mood = _get_mood(track)
		if mood:
			track_key = '%s----%s' % (track.artist, track.name)
			mood_by_track[track_key] = mood
	return mood_by_track


def diff_moody_tags(tracks, tags):
	tracks_by_key = {}
	for track in tracks:
		track_key = '%s----%s' % (track.artist, track.name)
		tracks_by_key.setdefault(track_key, [])
		tracks_by_key[track_key].append(track)
	
	differing_tracks = []
	for track_key, mood in tags.iteritems():
		for track in tracks_by_key.get(track_key, []):
			track_mood = _get_mood(track)
			if mood != track_mood:
				diff = {'track': track, 'mood': mood}
				differing_tracks.append(diff)
	
	return differing_tracks


def print_diff(differing_tracks):
	print 'Mood differences:'
	sorted_differing_tracks = sorted(differing_tracks, key=lambda d: d['track'].artist)
	for diff in sorted_differing_tracks:
		track, mood = diff['track'], diff['mood']
		lib_mood = _get_mood(track)
		print '%s - %s: In library: %s. From input: %s.' % (
				track.artist, track.name, lib_mood, mood)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    try:
        export, diff = _parse_args(argv)
    except Usage, err:
        print >>sys.stderr, err
        return 2
    
    logger.info('Opening iTunes library...')
    lib = pytunes.Library()
    logger.info('Loading all tracks...')
    all_tracks = list(lib.tracks)
    
    if export:
    	tags = get_moody_tags(all_tracks)
    	print simplejson.dumps(tags)
    
    if diff:
    	tags = simplejson.loads(sys.stdin.read())
    	differing_tracks = diff_moody_tags(all_tracks, tags)
    	print_diff(differing_tracks)


if __name__ == '__main__':
    sys.exit(main())
