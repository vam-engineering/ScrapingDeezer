import os
import requests
import pandas as pd
import re
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def extract_id(input_str):
    """Extracts the numerical ID from a given Deezer URL or accepts raw numeric IDs."""
    if input_str.isdigit():
        return input_str  # Directly return if input is a numeric ID
    match = re.search(r'/(\d+)$', input_str)
    return match.group(1) if match else None


def get_tracks(playlist_id, playlist_name):
    """Fetches tracks from a playlist and saves them to a CSV file."""
    base_url = f'https://api.deezer.com/playlist/{playlist_id}/tracks?limit=25'
    tracks = []
    index = 0

    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    while True:
        url_with_index = f'{base_url}&index={index}'
        try:
            response = session.get(url_with_index, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f'Error fetching tracks: {e}')
            return

        if not data.get('data'):
            break

        for track in data['data']:
            album_id = track['album'].get('id')
            album_info = get_album_details(album_id) if album_id else {}

            tracks.append({
                'Title': track['title'],
                'Title Short': track['title_short'],
                'Link': track['link'],
                'Duration': track['duration'],
                'Artist': track['artist'].get('name'),
                'Artist Link': track['artist'].get('link'),
                'Album': track['album'].get('title'),
                'Album Link': track['album'].get('tracklist'),
                'Album Release Date': album_info.get('release_date', 'Unknown'),
                'Album Genre': album_info.get('genre', 'Unknown')
            })

        index += 25  # Move to next batch

    df = pd.DataFrame(tracks)
    df.to_csv(f'playlists/{playlist_name}.csv', index=False)
    print(f'Playlist "{playlist_name}" saved.')


def get_album_details(album_id):
    """Fetches album details including release date and genre."""
    url = f'https://api.deezer.com/album/{album_id}'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            'release_date': data.get('release_date', 'Unknown'),
            'genre': data['genres']['data'][0]['name'] if data.get('genres') and data['genres']['data'] else 'Unknown'
        }
    except requests.exceptions.RequestException as e:
        print(f'Error fetching album details: {e}')
        return {}


def get_album_tracks(album_id):
    """Fetches tracks from an album and saves them to a CSV file."""
    url = f'https://api.deezer.com/album/{album_id}/tracks'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f'Error fetching album tracks: {e}')
        return

    if not data.get('data'):
        print("No tracks found in this album.")
        return

    tracks = []
    for track in data['data']:
        tracks.append({
            'Title': track['title'],
            'Title Short': track['title_short'],
            'Link': track['link'],
            'Duration': track['duration'],
            'Artist': track['artist'].get('name'),
            'Artist Link': track['artist'].get('link')
        })

    df = pd.DataFrame(tracks)
    df.to_csv(f'playlists/album_{album_id}.csv', index=False)
    print(f'Album "{album_id}" saved.')


def get_playlists(user_id):
    """Fetches all playlists from a user."""
    base_url = f'https://api.deezer.com/user/{user_id}/playlists?limit=25'
    index = 0

    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    if not os.path.exists('playlists'):
        os.makedirs('playlists')

    while True:
        url_with_index = f'{base_url}&index={index}'
        try:
            response = session.get(url_with_index, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f'Error fetching playlists: {e}')
            return

        if not data.get('data'):
            break

        for playlist in data['data']:
            playlist_id = playlist['id']
            playlist_name = playlist['title']
            get_tracks(playlist_id, playlist_name)

        index += 25  # Move to next batch

    print('All playlists have been saved.')


# User input: URL or raw ID
user_input = input('Enter a Deezer URL or ID: ').strip()

# Extract the ID
entity_id = extract_id(user_input)
if not entity_id:
    print('Invalid input. Could not extract ID.')
    exit()

# Determine if it's a user, playlist, or album
if 'album' in user_input or user_input.isdigit():
    print(f'The ID corresponds to an album. Fetching tracks...')
    get_album_tracks(entity_id)
elif 'playlist' in user_input or user_input.isdigit():
    print(f'The ID corresponds to a playlist. Fetching tracks...')
    get_tracks(entity_id, f'playlist_{entity_id}')
elif 'profile' in user_input or 'user' in user_input:
    print(f'The ID corresponds to a user. Fetching playlists...')
    get_playlists(entity_id)
else:
    print('Invalid input type. Please enter a valid Deezer album, playlist, or user profile URL or ID.')

print('Done.')
