import json
import time
import argparse
import psutil
import subprocess
import platform
import os


def memory_limit(process, max_memory):
    memory_usage = process.memory_info().rss

    if memory_usage > max_memory:
        process.terminate()
        return True

    return False


parser = argparse.ArgumentParser(description='Integer che rappresentano modi di esecuzione')
parser.add_argument('-type', type=int, help='Tipo di esecuzione')
parser.add_argument('-id', type=int, help='Id esecuzione', required=False)
parser.add_argument('-e1', type=str, help='Extra 1', required=False)
parser.add_argument('-e2', type=str, help='Extra 2', required=False)

args = parser.parse_args()

process_string = ''

if not os.path.exists('data'):
    os.makedirs('data')
if not os.path.exists('data/database.json'):
    with open('data/database.json', 'w') as f:
        json.dump({}, f)

if args.type == 1:
    process_string = 'python ./scraper/get_series.py'
elif args.type == 2:
    if args.id is None:
        print('Invalid id')
        exit(1)
    process_string = 'python ./scraper/parse_series.py -s ' + str(args.e1) + ' -e ' + str(args.e2) + ' -id ' + str(args.id)
elif args.type == 3:
    process_string = 'python ./scraper/download_episodes.py -c ' + str(args.e1)
elif args.type == 4:
    process_string = 'python ./scraper/get_serie.py -s ' + str(args.e1)
else:
    print('Invalid type')
    exit(1)

subproc = subprocess.Popen(process_string.split(' '))

if args.type == 1 or args.type == 3 or args.type == 4:
    out, err = subproc.communicate()
    if out:
        print("Output: ", out.decode())
    if err:
        print("Error: ", err.decode())

if args.type == 2:
    time.sleep(5)

    process = psutil.Process(subproc.pid)

    while True:
        if subproc.poll() is not None:
            break

        if memory_limit(process, 3000 * 1024 * 1024):  # 3000 MB
            print("Memory usage is too high, restarting...")
            try:
                with open(f'data/temp{args.id}.json', 'r') as f:
                    # get fid
                    file = json.load(f)
                    # kill it
                    p = psutil.Process(int(file['pid']))
                    p.terminate()
            except:
                pass

            #if on linux try to remove /tmp/*
            if platform.system() == 'Linux':
                try:
                    subprocess.Popen('rm -rf /tmp/*', shell=True)
                except:
                    pass

            subproc = subprocess.Popen(process_string.split(' '))
            process = psutil.Process(subproc.pid)

        time.sleep(1)
