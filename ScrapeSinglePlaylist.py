import requests
import pandas as pd

playlist_id = input('Playlist ID? \n Series of numbers to be found in the URL: ')

base_url = f'https://api.deezer.com/playlist/{playlist_id}'
url = f'https://api.deezer.com/playlist/{playlist_id}/tracks?limit=25'

tracks = []
index = 0

while True:
    url_with_index = f'{url}&index={index}'

    response = requests.get(url_with_index)
    data = response.json()

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception('HTTP request error:', response.status_code)

    # If no data is returned, exit the loop
    if not data['data']:
        break

    for track in data['data']:
        title = track['title_short']
        artist = track['artist'].get('name')
        tracks.append({'Title': title, 'Artist': artist})

    # Increment the index to fetch the next set of tracks
    index += 25

# Convert to Pandas DataFrame
df = pd.DataFrame(tracks)
# Save to CSV
df.to_csv('deezer_playlist.csv', index=False)
print('Playlist saved to deezer_playlist.csv')
