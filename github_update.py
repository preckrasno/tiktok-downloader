# github_update.py

from typing import List
import requests
import base64
import datetime
from settings import GITHUB_API_URL, GITHUB_API_TOKEN, GITHUB_API_USER_NAME, GITHUB_API_USER_EMAIL

headers = {
    'Authorization': f'Bearer {GITHUB_API_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
    'Content-Type': 'application/json'
}


def get_file() -> List[str]:
    # try get file
    try:
        response = requests.get(GITHUB_API_URL, headers=headers)
    except requests.exceptions.RequestException as e:
        print(e)
        return

    # get sha
    sha: str = response.json()['sha']
    # get content
    content: str = response.json()['content']
    # decode content from base64
    content: str = base64.b64decode(content).decode('utf-8')
    return [sha, content]


def update_file(sha: str, content: str):
    # current date and time
    # format %Y-%m-%d %H:%M:%S
    now: datetime = datetime.datetime.now()
    counter: int = 1

    # get first line of file
    first_line: str = content.splitlines()[0]

    # check if first line is not empty and contains counter, word 'start'
    is_not_empty: bool = bool(first_line)
    is_contains_counter: bool = first_line.split()[0].isdigit()
    is_contains_word_start: bool = first_line.split()[1] == 'start'

    if is_not_empty and is_contains_counter and is_contains_word_start:
        # get counter from first line
        # first line example: "45 start 2021-09-01 12:00:00" where 45 is counter and 2021-09-01 12:00:00 is date and time
        # date in format %Y-%m-%d %H:%M:%S
        counter = int(first_line.split()[0])
        # update counter
        counter += 1

    # append new line to content at the beginning
    content = f'{counter} start {now}\n{content}'

    # encode content to base64
    content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

    # data
    data: dict = {
        'message': 'update',
        'committer': {
            'name': GITHUB_API_USER_NAME,
            'email': GITHUB_API_USER_EMAIL,
        },
        'content': content,
        'sha': sha
    }

    # try update file
    try:
        response = requests.put(GITHUB_API_URL, headers=headers, json=data)
    except requests.exceptions.RequestException as e:
        print(e)
        return


if __name__ == '__main__':
    sha, content = get_file()
    update_file(sha, content)
