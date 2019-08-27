import requests
import json
import time
import os


# 读取配置文件
config_path = './config.json'
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

music_root = config['filename']['music_root']
api_address = config['api']['url']
context = {}

# 简单包装, 毕竟我只会调api嘛qaq
def api(subaddr, arg={}):
    target_addr = api_address + subaddr
    if not config['api']['cache']:
        arg['timestamp'] = time.time() # 加时间戳刷新缓存
    return requests.get(target_addr, params=arg, cookies=context['cookies_jar']).json()

# 登陆并保存api所需cookies
def login(phone, password):
    if 'cookies_jar' not in context:
        response = requests.get(f'{api_address}/login/cellphone', params={
            'phone': phone,
            'password': password,
        })
        if (response.json())['code'] == 200:
            context['cookies_jar'] = response.cookies
            print('Succ: Has login, saved cookies.')
        else:
            print('Fail: Phone or password wrong!')

# 主要是获得自己的userId
def get_self_info():
    context['user_id'] = api('/login/status')['profile']['userId'] 

# 获得自己创建的歌单
def get_self_playlist():
    return list(
        map(lambda x: {'name': x['name'], 'id': x['id']}, # 不要那些乱七八糟的信息
            filter(
                lambda x: x['creator']['userId'] == context['user_id'], # 获取属于自己创建的歌单
                api('/user/playlist', {'uid': context['user_id']})['playlist']
            )
        )
    )


# 获得某个歌单里所有歌的ID
def get_playlist_songs_id(playlist_id):
    return list(map(
        lambda x: x['id'],
        api('/playlist/detail', {'id': playlist_id})['playlist']['trackIds'] # 文档说trackIds才是完整的
    ))

# 根据歌单获得里面所有歌的相关数据
# 注意url接口返回的url只有20min有效期, 如果网速慢/歌单大的话可能下不完
# TODO 修复上面提到的问题
def get_playlist_songs(playlist_id):
    song_id = get_playlist_songs_id(playlist_id)
    ids = ','.join(map(lambda x: str(x), song_id))
    # 为了保险也sort一下
    details = sorted(
        map(lambda x: {
                'singer': ','.join(map(lambda y: y['name'], x['ar'])), # 多个歌手用逗号分割
                'name': x['name'], 'id': x['id'], 'rank': song_id.index(x['id'])
            },
            api('/song/detail', {'ids': ids})['songs']
        ), key=lambda x: x['rank']
    )
    # 这个接口返回的数据顺序是乱的, 调了半天emmm
    urls = sorted( 
        map(lambda x: { 'url': x['url'], 'ext': x['type'], 'id': x['id'], 'rank': song_id.index(x['id'])},
            api('/song/url', {'id': ids})['data']
        ), key=lambda x: x['rank']
    )
    return list(map(
        lambda t: {
            'singer': t[0]['singer'], 'name': t[0]['name'],
            'url': t[1]['url'], 'ext': t[1]['ext'], 'id': t[0]['id']
        }, zip(details, urls)
    ))

# 简单包装一下
def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# 很多歌名都包含奇奇怪怪的字符, 要判断替换
def change_name(raw_name):
    for rep in config['filename']['replace']:
        raw_name = raw_name.replace(rep[0], rep[1])
    return raw_name


import urllib3
if __name__ == '__main__':
    login(config['account']['phone'], config['account']['password'])
    get_self_info()
    http_pool = urllib3.PoolManager(num_pools=10) # urllib3下载貌似会快一点(但是sd卡写入慢啊emmm)
    fail_list = [] # 记录一波失效的歌
    playlist_index = 0
    for playlist in get_self_playlist():
        playlist_name = change_name(f'{playlist_index:02} - {playlist["name"]}')
        mkdir(os.path.join(music_root, playlist_name))
        songs = get_playlist_songs(playlist['id'])
        playlist_size = len(songs)
        song_index = 0

        for song in songs:
            real_index = 999 - (playlist_size - song_index) # 从999开始排, 可以方便地在顶部新加歌/删歌
            song_name = change_name(f'{real_index:03} - {song["name"]} - {song["singer"]}.{song["ext"]}')
            song_path = os.path.join(music_root, playlist_name, song_name)
            song_index = song_index + 1
            
            
            # 下过了
            if os.path.exists(song_path) and os.path.getsize(song_path) > 1024: # 大过 1KiB 才算下过
                print(f'Spik: {playlist_name} / {song_name}')
                continue
            
            # 你歌灰了
            if song['url'] == None:
                print(f'Fail: Can NOT download: {playlist_name} / {song_name}')
                fail_list.append({
                    'id': song['id'],
                    'name': song['name'],
                    'singer': song['singer'],
                    'playlist': playlist_name
                })
                continue
            
            print(f'Downloading: {playlist_name} / {song_name}', end="")

            # 下载
            response = http_pool.request('GET', song['url'])
            print('  [Connected]', end="") # 根据这行和下面一个print可以判断你sd卡的速度
            with open(song_path, 'wb') as f:
                f.write(response.data)
            response.release_conn()

            print(f'  [{os.path.getsize(song_path) / 1024 / 1024:3.2f} MiB]')

        playlist_index = playlist_index + 1
    
    # 下载完显示一下灰掉的歌
    print('Download finish.')
    for fail_song in fail_list:
        print(f'Fail: {fail_song["id"]} - {fail_song["name"]} - {fail_song["singer"]} in {fail_song["playlist"]}')
