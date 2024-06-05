import argparse
import os
import time
from queue import Queue

import requests
import random
import string
from concurrent.futures import ThreadPoolExecutor
from tinydb import TinyDB
from tqdm import tqdm

db = TinyDB('./data/database.json')
series_parsed_table = db.table('series_parsed')


def generate_user_agent():
    platforms = ['Windows NT 10.0; Win64; x64', 'Windows NT 10.0; Win64; x64; rv:100.0', 'X11; Linux x86_64',
                 'Macintosh; Intel Mac OS X 10_15_7']
    browsers = ['AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                'Gecko/20100101 Firefox/89.0', 'Gecko/20100101 Firefox/100.0']
    user_agents = []

    for _ in range(100):
        platform = random.choice(platforms)
        browser = random.choice(browsers)
        random_version = ''.join(random.choices(string.digits, k=2))
        user_agent = f'Mozilla/5.0 ({platform}) {browser} Version/{random_version}'
        user_agents.append(user_agent)

    return random.choice(user_agents)


def download_chunk(url, start, end, filename, queue):
    headers = {'Range': f'bytes={start}-{end}', 'User-Agent': generate_user_agent()}
    response = requests.get(url, headers=headers, stream=True)
    with open(filename, 'r+b') as fp:
        fp.seek(start)
        fp.write(response.content)
    queue.put(end - start)


def multi_thread_download(url, filename):
    response = requests.head(url, headers={'User-Agent': generate_user_agent()})
    file_size = int(response.headers.get('content-length', 0))
    part_size = int(1024 * 1024 * 1.5)  # Size of each chunk (1.5MB)

    # Create file of the same size as the one to be downloaded
    with open(filename, 'wb') as fp:
        fp.write(b'\0' * file_size)

    # Create ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        queue = Queue()
        futures = [executor.submit(download_chunk, url, start, start + part_size - 1, filename, queue)
                   for start in range(0, file_size, part_size)]

        with tqdm(total=file_size, ncols=70, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
            for _ in futures:
                pbar.update(queue.get())


def download_episodes(episodes):
    print('Starting download of episodes')
    for episode in episodes:
        directory = episode['video_url'].split('/')[-2]
        filename = episode['video_url'].split('/')[-1]

        if not os.path.exists(f'../../{directory}'):
            os.makedirs(f'../../{directory}')

        if not os.path.exists(f'../../{directory}/{filename}'):
            print(f'Starting download of {directory}/{filename}')
            multi_thread_download(episode['video_url'], f'../../{directory}/{filename}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-c', type=bool, help='Continuous', required=False)
    parser.add_argument('-m', type=int, help='Mode', required=False)
    args = parser.parse_args()

    if args.c is None:
        args.c = False

    if args.m is None or args.m == 1:
        def all_episodes():
            series = series_parsed_table.all()
            episodes = []

            for serie in series:
                for episode in serie["episodes"]:
                    if episode['video_url'] == '':
                        continue
                    else:
                        episodes.append(episode)

            download_episodes(episodes)

        all_episodes()

        if args.c:
            print('Waiting for new series')
            time.sleep(300)
            all_episodes()