import const
import urllib3
import requests


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def is_game_owned(game_url):
    """判定steam是否拥有该游戏"""
    try:
        resp = requests.get(
            url=game_url,
            headers=const.steam_headers,
            cookies=const.steam_cookies,
            verify=False
        )
        if resp is None or resp.text.find(const.steam_text_owned) == -1:
            return False
        return True
    except Exception as err:
        print(f'[ERROR]: {err}')
        return False
