import os

import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

user_id = input('Your user ID ? \n It can be found in the URL of your Deezer profile: ')
base_url = f'https://api.deezer.com/user/{user_id}/playlists?limit=25'

playlists = []
index_playlists = 0
# Playlists files will be saved in a separate folder
if not os.path.exists('playlists'):
    os.makedirs('playlists')

# Set up session with retries
session = requests.Session()
retry = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Scrape playlists
while True:
    url_playlists = f'{base_url}&index={index_playlists}'

    try:
        response_1 = session.get(url_playlists, timeout=10)
        response_1.raise_for_status()
        data_1 = response_1.json()
    except requests.exceptions.RequestException as e:
        print(f'Error during request: {e}')
        break

    if not data_1['data']:
        break

    for playlist in data_1['data']:
        playlist_name = playlist['title']
        url_tracks = playlist['tracklist']
        playlists.append({'Playlist title': playlist_name, 'Link': url_tracks})

        tracks = []
        index_tracks = 0

        # Scrape tracks in playlist
        while True:
            url_tracks_paged = f'{url_tracks}?limit=25&index={index_tracks}'
            try:
                response_2 = session.get(url_tracks_paged, timeout=10)
                response_2.raise_for_status()
                data_2 = response_2.json()
            except requests.exceptions.RequestException as e:
                print(f'Error during request: {e}')
                break

            if not data_2['data']:
                break

            for track in data_2['data']:
                title = track['title']
                title_short = track['title_short']
                link = track['link']
                duration = track['duration']
                artist_name = track['artist'].get('name')
                artist_link = track['artist'].get('link')
                album_name = track['album'].get('name')
                album_link = track['album'].get('link')
                tracks.append({
                    'Title': title,
                    'Title Short': title_short,
                    'Link': link,
                    'Duration': duration,
                    'Artist': artist_name,
                    'Artist Link': artist_link,
                    'Album': album_name,
                    'Album Link': album_link
                })

            index_tracks += 25  # Move to next batch of tracks

        # To DataFrame Pandas
        df = pd.DataFrame(tracks)
        # Save to CSV
        df.to_csv(f'playlists/{playlist_name}.csv', index=False)
        print(f'Playlist saved in {playlist_name}.csv')

    index_playlists += 25  # Move to next batch of playlists

print('Done.')
