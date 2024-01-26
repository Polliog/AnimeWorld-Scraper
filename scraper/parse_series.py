import argparse
import json
import multiprocessing as mp
import random
import string
import time
import traceback
import tracemalloc
import requests

from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from seleniumwire import webdriver
from tinydb import TinyDB, Query
from tinyrecord import transaction

db = TinyDB('./data/database.json')
parse_error_table = db.table('parse_error')
series_parsed_table = db.table('series_parsed')

options = Options()


# options.headless = True
# binary = FirefoxBinary("/usr/bin/firefox")
# options.binary = binary
# options.add_argument("--headless")

# logger = logging.getLogger('selenium')
# logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler('test.log')
# logger.addHandler(handler)

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


service = Service(executable_path="./geckodriver.exe", service_log_path='./data/geckodriver.log')


class SeriesParsedTable:
    @staticmethod
    def contains(query):
        # try a max of 15 times and wait 5 seconds between each try
        for i in range(15):
            try:
                return series_parsed_table.contains(query)
            except:
                time.sleep(5)
                continue
        else:
            raise Exception("Can't connect to database")

    @staticmethod
    def insert(query):
        for i in range(15):
            try:
                with transaction(series_parsed_table) as tr:
                    return tr.insert(query)
            except:
                time.sleep(5)
                continue
        else:
            raise Exception("Can't connect to database")

    @staticmethod
    def remove(query):
        # try a max of 15 times and wait 5 seconds between each try
        for i in range(15):
            try:
                return series_parsed_table.remove(query)
            except:
                time.sleep(5)
                continue
        else:
            raise Exception("Can't connect to database")


def parse_error(id):
    with transaction(series_parsed_table) as tr:
        tr.remove(Query().slug == id)
    with transaction(parse_error_table) as tr:
        tr.insert({'id': id})


def parse_series():
    parser = argparse.ArgumentParser(description='Integer che rappresentano modi di esecuzione')
    parser.add_argument('-s', type=int, help='Start', required=False)
    parser.add_argument('-e', type=int, help='End', required=False)
    parser.add_argument('-id', type=int, help='Id')

    args = parser.parse_args()

    if args.id is None:
        print("Invalid id")
        exit(1)

    print(args)

    tracemalloc.start()
    driver = webdriver.Firefox(service=service, options=options)
    pid = driver.service.process.pid

    # create temp file if not exists
    try:
        with open(f'./data/temp{args.id}.json', 'r') as f:
            pass
    except:
        with open(f'./data/temp{args.id}.json', 'w+') as f:
            json.dump({'pid': pid, 'lastId': ""}, f)

    lastId = ""

    # get last id from temp file
    with open(f'./data/temp{args.id}.json', 'r') as f:
        file = json.load(f)
        try:
            lastId = file['lastId']
        except:
            pass

    with open(f'./data/temp{args.id}.json', 'w+') as f:
        print(pid)
        # save pid in temp file and don't remove from file the last id
        json.dump({'pid': pid, 'lastId': lastId}, f)

    driver.install_addon('uBlock.xpi', temporary=True)

    with open('./data/series.json', 'r') as f:
        series = json.load(f)['data']
    if args.s is not None and args.e is not None:
        series = series[int(args.s):int(args.e)]
    elif args.s is not None:
        series = series[int(args.s):]
    elif args.e is not None:
        series = series[:int(args.e)]

    driver.get('https://www.animeworld.so')
    driver.execute_script("window.localStorage.setItem('defaultServer', '9');")
    driver.execute_script("window.localStorage.setItem('hentaiAlert', '1');")

    if lastId != "":
        for i in range(len(series)):
            if series[i].split('/')[-1] == lastId:
                series = series[i:]
                break

    for serie in series:
        series_id = serie.split('/')[-1]
        print(series_id)

        if SeriesParsedTable.contains(Query().slug == series_id):
            continue
        else:
            print(series_id)
            # save in temp file the id of the series
            with open(f'./data/temp{args.id}.json', 'w+') as f:
                json.dump({'pid': pid, 'lastId': series_id}, f)

        newSerie = {'slug': series_id, 'element_type': 'anime'}

        try:
            driver.get(serie)
        except:
            try:
                driver.quit()
                driver = webdriver.Firefox(service=service, options=options)
                driver.install_addon('uBlock.xpi', temporary=True)
                driver.get(serie)
            except:
                exit(1)

        time.sleep(2.5)

        # check if exist an element with id "404-gif-image-container"
        try:
            driver.find_element(by=By.ID, value="404-gif-image-container")
            parse_error(series_id)
            continue
        except:
            pass

        try:
            newSerie['main_url'] = driver.find_element(by=By.XPATH,
                                                       value="//div[@id='thumbnail-watch']/img").get_attribute('src')
        except:
            pass

        try:
            newSerie['title'] = driver.find_element(by=By.XPATH, value="//h2[@class='title']").text
        except:
            pass

        try:
            newSerie['description'] = driver.find_element(by=By.XPATH, value="//div[@class='desc']/div").text
        except:
            pass

        try:
            newSerie['mal_link'] = driver.find_element(by=By.ID, value="mal-button").get_attribute('href')
        except:
            pass

        try:
            info = \
                driver.find_elements(by=By.CLASS_NAME, value='info')[1].find_elements(by=By.TAG_NAME, value='div')

            for div in info:
                if div.find_elements(by=By.TAG_NAME, value='dl'):
                    info = div
                    break

            for dl in info.find_elements(by=By.TAG_NAME, value='dl'):
                dt = dl.find_elements(by=By.TAG_NAME, value='dt')
                dd = dl.find_elements(by=By.TAG_NAME, value='dd')
                for i in range(len(dt)):
                    if dt[i].text == 'Categoria:':
                        newSerie['sub_type'] = dd[i].text.lower()
                    elif dt[i].text == 'Audio:':
                        newSerie['country'] = dd[i].text.lower()[:2]
                        newSerie['subbed'] = 'sub' if dd[i].text != 'Italiano' else 'dub'
                    elif dt[i].text == 'Data di Uscita:':
                        newSerie['start_date'] = dd[i].text
                    elif dt[i].text == 'Studio:':
                        newSerie['studios'] = [dd[i].text]
                    elif dt[i].text == 'Genere:':
                        newSerie['genres'] = dd[i].text.split(', ')
                    elif dt[i].text == 'Durata:':
                        newSerie['episodes_duration'] = dd[i].text
                    elif dt[i].text == 'Episodi:':
                        newSerie['episodes_number'] = dd[i].text
                    elif dt[i].text == 'Stato:':
                        status_map = {'In Corso': 'airing', 'Finito': 'finished', 'Non rilasciato': 'announced'}
                        newSerie['status'] = status_map.get(dd[i].text, 'unknown')
        except Exception as e:
            traceback.print_exc()
            print("Errore: ", e)
            pass

        # if announce don't parse episodes

        episodes_links = []

        if newSerie['status'] != 'announced':
            try:
                newSerie['episodes'] = []
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
                    if episode["id"] == '':
                        continue

                    print("Episode: ", episode['number'])

                    try:

                        headers = {
                            'User-Agent': generate_user_agent()
                        }

                        req = requests.get(f'https://www.animeworld.so/api/episode/info?id={episode["id"]}',
                                           headers=headers)
                        data = req.json()
                        episode["video_url"] = data["grabber"]
                    except Exception as e:
                        traceback.print_exc()
                        print("Errore: ", e)
                        return

            except Exception as e:
                traceback.print_exc()
                print("Errore: ", e)
                parse_error(series_id)
                continue

        print(episodes_links)
        newSerie["episodes"] = episodes_links

        def saveInTable():
            try:
                SeriesParsedTable.insert(newSerie)
            except ValueError as ee:
                if "Document with ID" in str(ee):
                    print("Document with ID already exists, retrying...")
                    time.sleep(random.randint(1, 5))
                    saveInTable()
                    # save in temp file the id of the series
                    with open(f'./data/temp{args.id}.json', 'w+') as f:
                        json.dump({'pid': pid, 'lastId': series_id}, f)

        saveInTable()

        current, peak = tracemalloc.get_traced_memory()
        print(f"Current memory usage is {current / 10 ** 6}MB; Peak was {peak / 10 ** 6}MB")

    tracemalloc.stop()
    driver.quit()


if __name__ == '__main__':
    p = mp.Process(target=parse_series())
    p.start()
    p.join()
