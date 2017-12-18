import pathvalidate
import base64

from mutagen.id3 import ID3
from mutagen.id3 import ID3NoHeaderError
from mutagen.id3._frames import TPE1, APIC
from mutagen.mp4 import MP4, MP4Cover
from mutagen.easyid3 import EasyID3
import json
from pyDes import *
import urllib3
import urllib.request
import urllib3.request
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os

# Pre Configurations
urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
unicode = str
raw_input = input


def addtags(filename, json_data):
    try:
        audio = MP4(filename)
        audio['\xa9nam'] = unicode(json_data['song'])
        audio['\xa9ART'] = unicode(json_data['primary_artists'])
        audio['\xa9alb'] = unicode(json_data['album'])
        audio['aART'] = unicode(json_data['singers'])
        audio['\xa9wrt'] = unicode(json_data['music'])
        audio['desc'] = unicode(json_data['starring'])
        audio['\xa9gen'] = unicode(json_data['label'])
        # audio['cprt'] = track['copyright'].encode('utf-8')
        # audio['disk'] = [(1, 1)]
        # audio['trkn'] = [(int(track['track']), int(track['maxtracks']))]
        audio['\xa9day'] = unicode(json_data['year'])
        # if track['explicit']:
        #    audio['rtng'] = [(str(4))]
        cover_url = json_data['image'][:-11] + '500x500.jpg'
        fd = urllib.request.urlopen(cover_url)
        cover = MP4Cover(fd.read(), getattr(MP4Cover, 'FORMAT_PNG' if cover_url.endswith('png') else 'FORMAT_JPEG'))
        fd.close()
        audio['covr'] = [cover]
        audio.save()
    except:
        os.rename(filename, filename[:-3]+'mp3')
        filename = filename[:-3] + 'mp3'
        try:
            audio = ID3(filename)
        except ID3NoHeaderError:
            audio = ID3()

        audio.add(TPE1(encoding=3, text=unicode(json_data['singers'])))
        audio.save(filename)
        audio = EasyID3(filename)
        audio['title'] = unicode(json_data['song'])
        audio['albumartist'] = unicode(json_data['primary_artists'])
        audio['album'] = unicode(json_data['album'])
        #audio['aART'] = unicode(json_data['singers'])
        audio['copyright'] = unicode(json_data['music'])
        #audio['copyright'] = unicode(json_data['starring'])
        audio['genre'] = unicode(json_data['label'])
        audio['date'] = unicode(json_data['year'])
        audio.save()

def setProxy():
    base_url = 'http://h.saavncdn.com'
    proxy_ip = ''
    if ('http_proxy' in os.environ):
        proxy_ip = os.environ['http_proxy']
    proxies = {
        'http': proxy_ip,
        'https': proxy_ip,
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0'
    }
    return proxies, headers


def setDecipher():
    return des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)


def searchSongs(query):
    songs_json = []
    albums_json = []
    playLists_json = []
    topQuery_json = []
    respone = requests.get(
        'https://www.saavn.com/api.php?_format=json&query={0}&__call=autocomplete.get'.format(query))
    if respone.status_code == 200:
        respone_json = json.loads(respone.text.splitlines()[5])
        albums_json = respone_json['albums']['data']
        songs_json = respone_json['songs']['data']
        playLists_json = respone_json['playlists']['data']
        topQuery_json = respone_json['topquery']['data']
    return {"albums_json": albums_json,
            "songs_json": songs_json,
            "playLists_json": playLists_json,
            "topQuery_json": topQuery_json}


def getPlayList(listId):
    songs_json = []
    respone = requests.get(
        'https://www.saavn.com/api.php?listid={0}&_format=json&__call=playlist.getDetails'.format(listId), verify=False)
    if respone.status_code == 200:
        songs_json = json.loads(respone.text.splitlines()[4])
        songs_json = songs_json['songs']
    return songs_json


def getAlbum(albumId):
    songs_json = []
    respone = requests.get(
        'https://www.saavn.com/api.php?_format=json&__call=content.getAlbumDetails&albumid={0}'.format(albumId),
        verify=False)
    if respone.status_code == 200:
        songs_json = json.loads(respone.text.splitlines()[5])
        songs_json = songs_json['songs']
    return songs_json


def getSong(songId):
    songs_json = []
    respone = requests.get(
        'http://www.saavn.com/api.php?songid={0}&_format=json&__call=song.getDetails'.format(songId), verify=False)
    if respone.status_code == 200:
        print(respone.text)
        songs_json = json.loads(respone.text.splitlines()[5])
        songs_json = songs_json['songs']
    return songs_json


def getHomePage():
    playlists_json = []
    respone = requests.get(
        'https://www.saavn.com/api.php?__call=playlist.getFeaturedPlaylists&_marker=false&language=tamil&offset=1&size=10&_format=json',
        verify=False)
    if respone.status_code == 200:
        temp = respone.text.splitlines()
        playlists_json = json.loads(respone.text.splitlines()[2])
        playlists_json = playlists_json['featuredPlaylists']
    return playlists_json


def downloadSongs(songs_json,location):
    des_cipher = setDecipher()
    for obj in songs_json:
        enc_url = base64.b64decode(obj['encrypted_media_url'].strip())
        dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode('utf-8')
        dec_url = dec_url.replace('_96.mp4', '_320.mp4')
        if os.path.exists(location) is False:
            os.mkdir(location)
        fn = pathvalidate.sanitize_filename(obj['song'])
        filename = location+'/'+fn + '.m4a'
        if os.path.isfile(filename):
            print('song- {} already downloaded'.format(filename))
            continue
        if os.path.isfile(filename[:-3] + 'mp3'):
            print('song- {} already downloaded'.format(filename[:-3] + 'mp3'))
            continue

        http = urllib3.PoolManager()
        print('Downloading songs {} '.format(filename))
        response = http.request('GET', dec_url)
        with open(filename, 'wb') as f:
            f.write(response.data)
        response.release_conn()
        '''
        proxies, headers = setProxy()
        try:
            res = requests.get(dec_url, proxies=proxies, headers=headers)
        except Exception as e:
            print('Error accesssing website error: ' + e)
            sys.exit()
        '''
        addtags(filename, obj)
        print(filename, '\n')


if __name__ == '__main__':

    print('Enter the playlist or album name')
    q = input()
    queryresults = searchSongs(q)
    if len(queryresults['albums_json']) > 0 :
        valid_albumIds = []
        print('Album List')
        for album in queryresults['albums_json']:
            valid_albumIds.append(album['id'])
            print('Enter {} for download {} songs'.format(album['id'], album['title']))
        print('Enter x to list playlist')

        album_id = input()
        if album_id is not 'x':
            if album_id in valid_albumIds:
                songs = getAlbum(album_id)
                downloadSongs(songs,album_id)
            else:
                print('Invalid album Id specified, Try again')
    else:
        print('No Album to show')

    if len(queryresults['playLists_json']) > 0:
        valid_playListIds = []
        for playList in queryresults['playLists_json']:
            valid_playListIds.append(playList['id'])
            print('Enter {} for list {} songs'.format(playList['id'], playList['title']))

        playList_id = input()
        if playList_id in valid_playListIds:
            songs = getPlayList(playList_id)
            downloadSongs(songs, playList_id)

        else:
            print('Invalid playLists Id specified, Try again')
    else:
        print('No playList to show')