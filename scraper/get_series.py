import json
import time
import traceback

from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from seleniumwire import webdriver

options = Options()

service = Service(executable_path="./geckodriver.exe", service_log_path='./data/geckodriver.log')


def get_series():
    driver = webdriver.Firefox(service=service, options=options)
    try:
        driver.install_addon('uBlock.xpi', temporary=True)

        driver.get('https://www.animeworld.so/az-list')
        driver.set_page_load_timeout(60)

        print("Inizio scraping link serie")

        # read series.json
        try:
            with open('data/series.json', 'r') as f:
                series = json.load(f)
        except:
            with open('data/series.json', 'w') as f:
                json.dump({'data': [], 'page': 1}, f)
            with open('data/series.json', 'r') as f:
                series = json.load(f)

        series_urls = series['data']
        page = series['page']

        print("Pagina attuale: " + str(page))
        while page < 190:
            print("Pagina attuale: " + str(page))

            _series = driver.find_elements(by=By.XPATH, value="//a[@class='name']")
            for serie in _series:
                series_urls.append(serie.get_attribute('href'))

                # save series_urls and page in series.json
                series = {
                    'data': series_urls,
                    'page': page
                }

            try:
                page += 1
                driver.get(f'https://www.animeworld.so/az-list?page={page}')
                time.sleep(2.5)

                with open('data/series.json', 'w') as f:
                    json.dump(series, f, indent=4)
            except:
                break

        driver.quit()

        print("Fine scraping link serie")
        print("Rimozione serie duplicate")

        # remove duplicate series
        series_urls = list(dict.fromkeys(series_urls))

        # save series_urls in series.json
        series = {
            'data': series_urls,
            'page': page
        }

        with open('data/series.json', 'w') as f:
            json.dump(series, f, indent=4)


    except:
        traceback.print_exc()
        driver.quit()
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == '__main__':
    get_series()
