import pay
import time
import util
import const
import urllib3
import requests
from config import configs
from bs4 import BeautifulSoup
from util import load_cache, save_cache, send_email


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_can_buy_from_steam(url, headers, cookies):
    """爬取steam游戏页面并判定是否可购买"""
    resp = requests.get(url, headers=headers, cookies=cookies, verify=False)
    data = resp.text

    owned = False
    limited = False
    is_dlc = False
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
        is_dlc = True

    if data.find(const.steam_text_play) != -1 and soup.find(class_=const.steam_class_free).get_text(strip=True) == const.steam_text_free:
        print('Free')
        free = True

    must_card = configs.get_filter_config('must_have_card', False)
    must_free = configs.get_filter_config('must_not_free', False)

    return not owned and not limited and not is_dlc and (card or not must_card) and not (free and must_free)


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


if __name__ == '__main__':
    sort_key        = configs.get_base_config('sort_key', '')
    page_size       = configs.get_base_config('page_size', 0)
    loop_sleep_time = configs.get_base_config('loop_sleep_time', 0)

    max_price       = configs.get_filter_config('max_price', 0)
    max_discount    = configs.get_filter_config('max_discount', 0)
    must_have_card  = configs.get_filter_config('must_have_card', False)
    must_not_free   = configs.get_filter_config('must_not_free', False)

    max_budget      = configs.get_pay_config('max_budget', 0)
    max_order       = configs.get_pay_config('max_order', 0)
    confirm_pause   = configs.get_pay_config('confirm_pause', True)

    buy_list = []

    while True:
        next_loop = False

        try:
            expired = requests.get(
                configs.get_base_config('verify_url', ''),
                headers = const.steam_headers,
                cookies = const.steam_cookies,
                verify  = False
            )

            if expired is None or expired.text.find(const.steam_text_owned) == -1:
                print('Steam Cookie Expired, Please Login')
                exit(0)
        except Exception as err:
            print(f'[ERROR]: {err}')
            print('Steam Cookie Expired, Please Login')
            exit(0)

        cache       = load_cache(must_have_card, must_not_free)
        page_number = configs.get_base_config('page_number', 1)
        max_page    = configs.get_base_config('max_page', 1)

        try:
            while max_page != 0:
                print('\nPAGE NUMBER:', page_number)
                rank_query = {
                    'pageNumber': page_number,
                    'pageSize'  : page_size,
                    'sort'      : sort_key,
                    'order'     : 'asc',
                    'startDate' : '',
                    'endDate'   : '',
                }

                py_resp = requests.get(
                    url     = const.py_rank_url,
                    params  = rank_query,
                    headers = const.py_headers,
                    cookies = const.py_cookies
                )

                content = util.get_json_value(py_resp.json(), ['result', 'content'], [])
                if len(content) == 0:
                    print('Py Cookie Expired, Please Login')
                    exit(0)

                cnt = 1
                page_number += 1
                max_page -= 1

                for info in content:
                    if pay.total_price >= max_budget or pay.total_order >= max_order:
                        print(f'Out of Budget: {pay.total_price}r/{max_budget}r {pay.total_order}/{max_order}')
                        save_cache(cache, must_have_card, must_not_free)
                        util.print_buy_list(buy_list)
                        exit(0)

                    py_name = util.get_json_value(info, ['gameNameCn'], '')
                    if py_name == '' or py_name is None:
                        py_name = util.get_json_value(info, ['gameName'], '')
                    print('=' * 10, f'{cnt}.', py_name, '=' * 10)

                    target_url = util.get_json_value(info, ['gameUrl'], '')
                    game_id = util.get_json_value(info, ['id'], '')

                    buy_game_info = {
                        'name'          : py_name,
                        'steam'         : target_url,
                        'py'            : const.py_detail_url + game_id,
                        'py_price'      : util.get_json_value(info, ['keyTxAmt'], ''),
                        'steam_price'   : util.get_json_value(info, ['oriPrice'], ''),
                        'discount'      : util.get_json_value(info, ['keyDiscount'], ''),
                    }

                    if get_can_buy_from_steam_with_cache(target_url, const.steam_headers, const.steam_cookies, cache):
                        util.print_buy_game(buy_game_info)
                        if float(buy_game_info['py_price']) > max_price:
                            print(f'CDK Price {buy_game_info['py_price']} > Max Price {max_price}')
                            if sort_key == const.sort_key_price:
                                next_loop = True
                                break
                        elif float(buy_game_info['discount']) > max_discount:
                            print(f'CDK Discount {buy_game_info['discount']} > Max Discount {max_discount}')
                            if sort_key == const.sort_key_discount:
                                next_loop = True
                                break
                        else:
                            if configs.get_pay_config('auto_pay', False):
                                success, msg, order_price = pay.pay_order(
                                    game_id,
                                    max_price,
                                    max_discount,
                                    buy_game_info['steam_price'],
                                    confirm_pause
                                )
                                if success:
                                    buy_list.append(buy_game_info)
                                    print(f'Success: {order_price}r')
                                    if configs.get_email_config('auto_email', False):
                                        send_email(
                                            const.email_title,
                                            f'{buy_game_info['name']}' +
                                            f'\nPrice：{order_price}r' +
                                            f'\nSteam：{buy_game_info['steam_price']}' +
                                            f'\nLink：{buy_game_info['steam']}' +
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
                                    if configs.get_pay_config('pause_beep', False):
                                        util.beep()
                                    input('Press Enter to Continue: ')


                    print('=' * 10, f'{cnt}.', py_name, '=' * 10)
                    print()
                    cnt += 1

                util.print_buy_list(buy_list)

                if next_loop:
                    break

        finally:
            save_cache(cache, must_have_card, must_not_free)

        if loop_sleep_time > 0:
            time.sleep(loop_sleep_time)
        else:
            break
