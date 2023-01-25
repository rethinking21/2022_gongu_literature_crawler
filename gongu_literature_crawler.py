import os
import csv
import pprint
import atexit
import selenium
from selenium import webdriver
from gongu_modules import gongu_search as GS
from gongu_modules import  viewer_crawler as VC
# csv(tsv) format : file_number, writer, name, context[...]

# region setting
DRIVER_SHOW: bool = True
DRIVER_PATH = r'./data/chromedriver.exe'
DATASET_PATH = r'./datasets'
SIZE_MAX = 5 * 10 ** 7
TAG = {
    "#시 ": "add",
    "#번역 ": "remove",
    "#번역시 " : "remove",
    "#정형시 ": "remove",
    "#초등학교 ": "tag school",
    "#학교 ": "tag school"
}

chrome_options: webdriver.ChromeOptions = None
driver: webdriver.Chrome = None
# endregion

# region selenium


def close_webdriver() -> None:
    global driver
    if driver is not None:
        driver.quit()
        print("Chrome Closed Safely(Enter to Quit)")
    _ = input()
    return


def open_webdriver() -> None:
    global driver, chrome_options, DRIVER_SHOW, DRIVER_PATH

    chrome_options = webdriver.ChromeOptions()
    if not DRIVER_SHOW:
        chrome_options.add_argument("headless")
    try:
        driver = webdriver.Chrome(DRIVER_PATH, options=chrome_options)
        atexit.register(close_webdriver)
    except selenium.common.exceptions.SessionNotCreatedException:
        print("!! Chrome Driver must be installed in right version.")
        print(f"!! Please check driver in {DRIVER_PATH} than update it\n!!")
        print("!! Check Chrome version in Chrome : chrome://settings/help")
        print("!! Download Chrome : https://chromedriver.chromium.org/downloads")

    driver.set_window_size(600, 1200)
    driver.implicitly_wait(2)

# endregion

# region csv writer


def write_csv_poet(poet_info: dict, number: int = 0):
    global driver, DATASET_PATH
    texts = VC.find_sentences_in_url(driver, poet_info['number'], poet_info['writer'])
    print(len(texts), 'line(s) found')
    if len(texts) <= 2:
        print("ignore this page")
    else:
        print("saving csv file. |", number, "writer", poet_info['writer'],
              ", name :", poet_info['name'],
              ", copyright_show :", poet_info['copyright_show'],
              ", copyright_profit : ", poet_info['copyright_profit'])
        for csv_path in find_paths_csv(poet_info):
            f = open(csv_path, 'a+', encoding='utf-8')
            wr = csv.writer(f, delimiter='\t')
            wr.writerow([poet_info['number'], poet_info['writer'], poet_info['name']
                         , *texts])
            f.close()


def find_paths_csv(poet_info: dict) -> list:
    global DATASET_PATH, SIZE_MAX
    output = []
    copyright_name: str
    if poet_info['copyright_show']:
        if poet_info['copyright_profit']:
            copyright_name = 'BY'
        else:
            copyright_name = 'BY_NC'
    else:
        copyright_name = 'free_use'
    div_path_name = f'{DATASET_PATH}/{copyright_name}'

    tag_list = []
    if len(poet_info['tag']) == 0:
        tag_list.append('default')
    else:
        tag_list.extend(poet_info['tag'])

    for tag_name in tag_list:
        files = sorted([filename for filename in os.listdir(div_path_name)
                 if (tag_name in filename) and ('.tsv' in filename)])
        if len(files) == 0 or os.path.getsize(f'{div_path_name}/{files[-1]}') > SIZE_MAX:
            output.append(f'{div_path_name}/{tag_name}_{len(files) + 1:0>2}.csv')
        else:
            output.append(f'{div_path_name}/{files[-1]}')
    return output
# endregion


open_webdriver()


for page_number in range(100, 0, -1):
    print(f'@search {page_number} page..')
    blocks = GS.find_blocks_in_page(driver, page_number, TAG)
    print(f'@{len(blocks)} blocks found')
    for block in blocks:
        write_csv_poet(block, page_number)

print("@data crawl successfully")
_ = input()
