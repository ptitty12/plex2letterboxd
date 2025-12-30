"""Export watched Plex movies to the Letterboxd import format."""
import argparse
import configparser
import csv
import sys

from plexapi.server import PlexServer


def parse_args():
    parser = argparse.ArgumentParser(
        description='Export watched Plex movies to the Letterboxd import '
                    'format.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--ini', default='config.ini',
                        help='config file')
    parser.add_argument('-o', '--output', default='letterboxd.csv',
                        help='file to output to')
    parser.add_argument('-s', '--sections', default=['Movies'], nargs='+',
                        help='sections to grab from')
    parser.add_argument('-m', '--managed-user',
                        help='name of managed user to export')
    parser.add_argument('-w', '--watched-after',
                        help='only return movies watched after the given time [format: YYYY-MM-DD or 30d]')
    return parser.parse_args()


def parse_config(ini):
    """Read and validate config file."""
    config = configparser.ConfigParser()
    config.read(ini)
    auth = config['auth']
    missing = {'baseurl', 'token'} - set(auth.keys())
    if missing:
        print(f'Missing the following config values: {missing}')
        sys.exit(1)
    return auth


def get_external_ids(movie):
    """Extract IMDb and TMDB IDs from Plex GUIDs."""
    imdb_id = None
    tmdb_id = None

    for guid in (g.id for g in movie.guids):
        if guid.startswith('imdb://'):
            imdb_id = guid.replace('imdb://', '')
        elif guid.startswith('tmdb://'):
            tmdb_id = guid.replace('tmdb://', '')

    return imdb_id, tmdb_id


def write_csv(sections, output, args):
    """Generate Letterboxd import CSV."""
    with open(output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Title',
            'Year',
            'imdbID',
            'tmdbID',
            'Rating10',
            'WatchedDate'
        ])

        count = 0
        for section in sections:
            filters = {'unwatched': False}
            if args.watched_after:
                filters['lastViewedAt>>'] = args.watched_after

            for movie in section.search(sort='lastViewedAt', filters=filters):
                imdbID, tmdbID = get_external_ids(movie)

                date = None
                if movie.lastViewedAt is not None:
                    date = movie.lastViewedAt.strftime('%Y-%m-%d')

                rating = movie.userRating
                if rating is not None:
                    rating = f'{rating:.0f}'

                writer.writerow([
                    movie.title,
                    movie.year,
                    imdbID,
                    tmdbID,
                    rating,
                    date
                ])
                count += 1

    print(f'Exported {count} movies to {output}.')


def main():
    args = parse_args()
    auth = parse_config(args.ini)

    plex = PlexServer(auth['baseurl'], auth['token'])

    if args.managed_user:
        myplex = plex.myPlexAccount()
        user = myplex.user(args.managed_user)
        token = user.get_token(plex.machineIdentifier)
        plex = PlexServer(auth['baseurl'], token)

    sections = [plex.library.section(s) for s in args.sections]
    write_csv(sections, args.output, args)


if __name__ == '__main__':
    main()
