import pay
import time
import util
import const
import requests
from config import configs
from bs4 import BeautifulSoup
from util import load_cache, save_cache, send_email


def get_can_buy_from_steam(url, headers, cookies):
    """爬取steam游戏页面并判定是否可购买"""
    resp = requests.get(url, headers=headers, cookies=cookies)
    data = resp.text

    owned = False
    limited = False
    isDLC = False
    card = False
    free = False

    soup = BeautifulSoup(data, 'html.parser')

    gameName = soup.find(id=const.steam_id_name).get_text(strip=True)
    print('Steam Game Name:', gameName)

    if data.find(const.steam_text_owned) != -1:
        print('Owned')
        owned = True

    if data.find(const.steam_text_limited) != -1 or data.find(const.steam_text_learning) != -1:
        print('Limited')
        limited = True

    if data.find(const.steam_text_card) != -1:
        print('Card')
        card = True

    if data.find(const.steam_text_dlc) != -1 or data.find(const.steam_text_soundtrack) != -1:
        print('DLC')
        isDLC = True

    if data.find(const.steam_text_play) != -1 and soup.find(class_=const.steam_class_free).get_text(strip=True) == const.steam_text_free:
        print('Free')
        free = True

    must_card = configs.get_filter_config('must_have_card', False)
    must_free = configs.get_filter_config('must_not_free', False)

    return not owned and not limited and not isDLC and (card or not must_card) and not (free and must_free)


def get_can_buy_from_steam_with_cache(url, headers, cookies, cacheInfo):
    """带多文件缓存的 get_can_buy_from_steam"""
    if url in cacheInfo:
        print(f'[CACHE] {url} -> False')
        return False

    try:
        result = get_can_buy_from_steam(url, headers, cookies)
        if result is False:
            cacheInfo[url] = False
        return result
    except Exception as e:
        if const.steam_err_lock in str(e):
            cacheInfo[url] = False
        print(f'[ERROR] {url}:', e)
        return False


def print_buy_game(game):
    """格式化输出游戏"""
    print(
        'Name:', game['name'],
        'CDK:', game['py_price'],
        'Steam:', game['steam_price'],
        'Discount:', game['discount'],
        game['steam'], game['py']
    )


def print_buy_list(buy_list):
    """格式化输出已购买列表"""
    print()
    print('=' * 20, 'Buy List', '=' * 20)
    print(f'Total: {len(buy_list)}')

    for game in buy_list:
        print_buy_game(game)

    print('=' * 20, 'Buy List', '=' * 20)
    print()


if __name__ == '__main__':
    sort_key = configs.get_base_config('sort_key', '')
    page_size = configs.get_base_config('page_size', 0)
    loop_sleep_time = configs.get_base_config('loop_sleep_time', 0)

    max_price = configs.get_filter_config('max_price', 0)
    max_discount = configs.get_filter_config('max_discount', 0)
    must_have_card = configs.get_filter_config('must_have_card', False)
    must_not_free = configs.get_filter_config('must_not_free', False)

    max_budget = configs.get_pay_config('max_budget', 0)
    max_order = configs.get_pay_config('max_order', 0)
    confirm_pause = configs.get_pay_config('confirm_pause', True)

    buyList = []

    while True:
        next_loop = False

        try:
            expired = requests.get(
                configs.get_base_config('verify_url', ''),
                headers=const.steam_headers,
                cookies=const.steam_cookies
            )

            if expired is None or expired.text.find(const.steam_text_owned) == -1:
                print('Cookie Expired, Please Login')
                exit(0)
        except Exception as err:
            print(f'[ERROR]: {err}')
            print('Cookie Expired, Please Login')
            exit(0)

        cache = load_cache(must_have_card, must_not_free)
        page_number = configs.get_base_config('page_number', 1)
        max_page = configs.get_base_config('max_page', 1)

        try:
            while max_page != 0:
                print('\nPAGE NUMBER:', page_number)
                cnt = 1
                page_number += 1
                max_page -= 1

                rank_query = {
                    'pageNumber': page_number,
                    'pageSize': page_size,
                    'sort': sort_key,
                    'order': 'asc',
                    'startDate': '',
                    'endDate': '',
                }

                pyResp = requests.get(
                    url=const.py_rank_url,
                    params=rank_query,
                    headers=const.py_headers,
                    cookies=const.py_cookies
                ).json()

                for info in util.get_json_value(pyResp, ['result', 'content']):
                    if pay.totalPrice >= max_budget or pay.totalOrder >= max_order:
                        print(f'Out of Budget: {pay.totalPrice}r/{max_budget}r {pay.totalOrder}/{max_order}')
                        save_cache(cache, must_have_card, must_not_free)
                        print_buy_list(buyList)
                        exit(0)

                    pyName = util.get_json_value(info, ['gameNameCn'], '')
                    if pyName == '' or pyName is None:
                        pyName = util.get_json_value(info, ['gameName'], '')
                    print('=' * 10, f'{cnt}.', pyName, '=' * 10)

                    targetURL = util.get_json_value(info, ['gameUrl'], '')
                    gameID = util.get_json_value(info, ['id'], '')

                    buyGameInfo = {
                        'name': pyName,
                        'steam': targetURL,
                        'py': 'https://steampy.com/cdkDetail?name=cn&gameId=' + gameID,
                        'py_price': util.get_json_value(info, ['keyTxAmt'], ''),
                        'steam_price': util.get_json_value(info, ['oriPrice'], ''),
                        'discount': util.get_json_value(info, ['keyDiscount'], ''),
                    }

                    if get_can_buy_from_steam_with_cache(targetURL, const.steam_headers, const.steam_cookies, cache):
                        print_buy_game(buyGameInfo)
                        if float(buyGameInfo['py_price']) > max_price:
                            print(f'CDK Price {buyGameInfo["py_price"]} > Max Price {max_price}')
                            if sort_key == const.sort_key_price:
                                next_loop = True
                                break
                        elif float(buyGameInfo['discount']) > max_discount:
                            print(f'CDK Discount {buyGameInfo["discount"]} > Max Discount {max_discount}')
                            if sort_key == const.sort_key_discount:
                                next_loop = True
                                break
                        else:
                            if configs.get_pay_config('auto_pay', False):
                                success, msg, orderPrice = pay.pay_order(
                                    gameID,
                                    max_price,
                                    max_discount,
                                    buyGameInfo['steam_price']
                                )
                                if success:
                                    buyList.append(buyGameInfo)
                                    print(f'Success: {orderPrice}r')
                                    if configs.get_email_config('auto_email', False):
                                        send_email(
                                            const.email_title, f'{buyGameInfo['name']}' +
                                            f'\nPrice：{orderPrice}r' +
                                            f'\nSteam：{buyGameInfo['steam_price']}' +
                                            f'\nLink：{buyGameInfo['steam']}' +
                                            const.email_notify,
                                            configs.get_email_config('email_addr', []),
                                            configs.get_email_config('smtp_from', ''),
                                            configs.get_email_config('smtp_server', ''),
                                            configs.get_email_config('smtp_port', 0),
                                            configs.get_email_config('smtp_pwd', '')
                                        )
                                else:
                                    print(f'Failed: {msg}')
                                if confirm_pause:
                                    input('Press Enter to Continue: ')


                    print('=' * 10, f'{cnt}.', pyName, '=' * 10)
                    print()
                    cnt += 1

                print_buy_list(buyList)

                if next_loop:
                    break

        finally:
            save_cache(cache, must_have_card, must_not_free)

        if loop_sleep_time > 0:
            time.sleep(loop_sleep_time)
        else:
            break
