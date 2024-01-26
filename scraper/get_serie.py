import argparse
import random
import string
import time
import json

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from scraper.download_episodes import download_episodes
from seleniumwire import webdriver

service = Service(executable_path="./geckodriver.exe", service_log_path='./data/geckodriver.log')

options = Options()


# options.add_argument("--headless")


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


def get_serie():
    parser = argparse.ArgumentParser(description='Link serie')
    parser.add_argument('-s', type=str, help='Link serie', required=True)

    args = parser.parse_args()

    if args.s is None:
        print('Invalid link')
        exit(1)

    print("Getting episodes")

    driver = webdriver.Firefox(service=service, options=options)
    driver.install_addon('uBlock.xpi', temporary=True)

    time.sleep(1.5)

    driver.get(args.s)

    driver.execute_script("window.localStorage.setItem('defaultServer', '9');")
    driver.execute_script("window.localStorage.setItem('hentaiAlert', '1');")

    try:
        episodes = []
        server_tabs = \
            driver.find_element(by=By.ID, value='animeId').find_elements(by=By.TAG_NAME, value='div')[
                0].find_elements(
                by=By.TAG_NAME, value='span')[1]
        for span in server_tabs.find_elements(by=By.TAG_NAME, value='span'):
            if 'animeworld' in span.text.lower():
                if span.get_attribute('class') == 'tab server-tab active':
                    break
                span.click()
                break
        else:
            server_tabs.find_elements(by=By.TAG_NAME, value='span')[0].click()

        time.sleep(1)

        server_episodes = \
            driver.find_element(by=By.ID, value='animeId').find_elements(by=By.TAG_NAME, value='div')[
                1]

        for div in server_episodes.find_elements(by=By.TAG_NAME, value='div'):
            if div.get_attribute('class') == 'server active':
                episodes_ul = div.find_elements(by=By.TAG_NAME, value='ul')
                break

        episodes_links = []

        for ul in episodes_ul:
            for li in ul.find_elements(by=By.TAG_NAME, value='li'):
                a = li.find_element(by=By.TAG_NAME, value='a')
                data = {
                    'url': a.get_attribute('href'),
                    # get id from https://www.animeworld.so/play/hackquantum.0n6TG/4wYVD (4wYVD)
                    'id': "",
                    'number': a.text if a.text else a.get_attribute('data-num'),
                    'video_url': ''
                }

                try:
                    data['id'] = a.get_attribute('href').split('/')[-1]
                except:
                    pass

                episodes_links.append(data)

        for episode in episodes_links:
            try:
                headers = {
                    'User-Agent': generate_user_agent()
                }

                req = requests.get(f'https://www.animeworld.so/api/episode/info?id={episode["id"]}',
                                   headers=headers)
                data = req.json()
                episode["video_url"] = data["grabber"]
            except Exception as e:
                print("Errore: ", e)
                return

        episodes_parsed = []
        for episode in episodes_links:
            episodes_parsed.append({'video_url': episode['video_url']})

        driver.quit()

        download_episodes(episodes_links)

        print("Episodi Scaricati")
    except:
        pass


if __name__ == '__main__':
    get_serie()
