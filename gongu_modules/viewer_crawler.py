import re
import time
import numpy as np
import selenium
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

line_diff = 0.5


def viewer_url(number: int) -> str:
    return f"https://gongu.copyright.or.kr/gongu/cmmn/docViewer/viewer.do?wrtSn={number}&fileSn=1"


def wait_until_load(driver: webdriver.Chrome, sleep: int = 0.1, implicitly_wait: int = 2) -> None:
    while 'viewer/skin' in driver.current_url:
        time.sleep(sleep)
    time.sleep(implicitly_wait)

# region find sentence


def find_sentences_in_url(driver: webdriver.Chrome, number: int, writer: str) -> list:
    output = []

    driver.get(viewer_url(number))
    for page_element in driver.find_elements(By.CLASS_NAME, "annotationlayer"):
        result = find_sentences_in_content_page(page_element)
        if len(result) != 0:
            output.extend(result)
    if len(output) == 0:
        return output
    left_min = min([line[1] for line in output])
    output = [line[0] for line in output if (writer not in line[0]) and  line[1] < left_min * 1.5]
    return output


def find_sentences_in_content_page(page_element) -> tuple:
    texts = []
    position_list = []
    try:
        for text_element in page_element.find_elements(By.CLASS_NAME, "text"):
            texts.append(text_element.get_attribute('data-char'))
            position_list.append(
                tuple(map(float, re.findall('[0-9.]+', text_element.get_attribute("style")))))
    except selenium.common.exceptions.StaleElementReferenceException:
        return ()
    if len(position_list) != 0:
        output = char_merger(texts, np.array(position_list))
        output = filter_lines(output)
        return output
    else:
        return ()
# endregion

# region merge and filter


def char_merger(texts: list, position: np.ndarray) -> tuple:
    position_normal: np.ndarray
    if position.ndim < 2:
        position_normal = (position / np.mean(position))[:, 0:2]
    else:
        position_normal = (position / np.mean(position[:, -1].T))[:, 0:2]
    position = np.concatenate((position_normal, position[:, 0:3]), axis=1)
    position_diff = np.abs(position - np.vstack((position[1:], position[-1:])))

    sentence_output, left_output = [], []
    current_text = ''

    index_list = [0]
    index_list.extend([index + 1
                       for index in range(len(texts))
                       if position_diff[index, 1] > line_diff])
    index_list.append(len(texts))
    index_list = [index_list[index]
                  for index in range(0, len(index_list) - 1)
                  if index_list[index + 1] - index_list[index] >= 3]
    index_list.append(len(texts))
    for index in range(len(index_list) - 1):
        sentence_output.append(''.join(texts[index_list[index]:index_list[index+1]]))
        left_output.append(position_normal[index_list[index] + 1, 0])

    return tuple(zip(sentence_output, left_output))


def filter_lines(lines: tuple) -> tuple:
    check = [(change_line(line[0]), line[1]) for line in lines]
    check = [line for line in check if len(line[0]) >= 3]
    if len(lines) == 0 or len(check) / len(lines) < 0.51:
        return ()
    else:
        return tuple(check)


def change_line(line: str) -> str:
    output = ''.join([char for char in line
                      if ("가" <= char <= '힣') or (char in '1223456789,.?!ㅡ ')])
    hangul = ''.join([char for char in line if ("가" <= char <= '힣')])
    if len(line) == 0 or len(output) / len(line) < 0.51:
        return ''
    elif len(hangul) <= 3:
        return ''
    elif '<' in line:
        return ''
    else:
        return output
# endregion
