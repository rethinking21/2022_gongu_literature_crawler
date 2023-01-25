import re
import selenium
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


def gongu_search_url(number: int) -> str:
    return f"https://gongu.copyright.or.kr/gongu/wrt/wrtCl/listWrtText.do?menuNo=200019&sortSe=date&licenseCd=&searchWrd=%EC%8B%9C&pageUnit=100&pageIndex={number}"


def find_blocks_in_page(driver: webdriver.Chrome, number: int, tags: dict = {}) -> list:
    output = []

    driver.get(gongu_search_url(number))
    bbs_element = driver.find_element(by=By.CLASS_NAME, value='bbsList')
    elements = bbs_element.find_elements(by=By.CSS_SELECTOR, value='#contents > div.bbsList.style2.wrt > ul > li')
    for element in elements:
        copyright_useful, copyright_profit, copyright_show = check_copyright(element)
        if copyright_useful:
            useful, tagset = check_tags(element, tags=tags)
            name = element.find_element(by=By.CLASS_NAME, value='tit').text
            if useful:
                block_info = {'number': int(find_link(element)), 'writer': find_writer(element), 'name': name,
                              'copyright_show': copyright_show, 'copyright_profit': copyright_profit, 'tag': tagset}
                output.append(block_info)
    return output

# region checking function


def check_tags(block_element, tags: dict = {}) -> tuple:
    output, tag = False, set()
    tag_element = block_element.find_element(by=By.CLASS_NAME, value='tag2')
    tag_text = tag_element.text + ' '

    for tag_name, action in tags.items():
        if tag_name in tag_text:
            if action == "add":
                output = True
            if action == "remove":
                return False, set()
            if "tag" in tag_name:
                tag.update({tag_name.split()[1]})
        else:
            if action == "must":
                return False, set()

    return output, tag


def check_copyright(block_element) -> tuple:
    copyright_text = block_element.find_element(by=By.CLASS_NAME, value='img_cc').get_attribute('alt')

    if '자유이용' in copyright_text:
        return True, True, False
    elif 'CC' in copyright_text:
        if '변경금지' in copyright_text:
            return False, False, False
        if '동일' in copyright_text:
            return False, False, False
        profit: bool = '비영리' not in copyright_text
        show: bool = '표시' in copyright_text
        print(copyright_text, True, profit, show)
        return True, profit, show
    else:
        return False, False, False

# endregion

# region find function


def find_link(block_element) -> str:
    try:
        link_element = block_element.find_element(by=By.CLASS_NAME, value='b-view').get_attribute('href')
    except NoSuchElementException:
        return ''
    else:
        number = re.findall('[0-9]+', link_element)
        if len(number) != 0:
            return number[0]
        else:
            return ''


def find_writer(block_element) -> str:
    try:
        return block_element.find_element(by=By.CLASS_NAME, value='ico_person').text
    except NoSuchElementException:
        return ''

# endregion
