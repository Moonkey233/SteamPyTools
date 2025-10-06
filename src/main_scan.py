import time
import util
import const
import py_api
import urllib3
import steam_api
import requests
from config import configs
from bs4 import BeautifulSoup


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

have_card = False

def get_can_buy_from_steam(url, headers, cookies):
    """爬取steam游戏页面并判定是否可购买"""
    global have_card
    have_card = False
    resp = requests.get(url, headers=headers, cookies=cookies, verify=False)
    data = resp.text

    owned = False
    limited = False
    is_dlc = False
    card = False
    free = False

    soup = BeautifulSoup(data, 'html.parser')

    game_name = soup.find(id=const.steam_id_name).get_text(strip=True)
    print('[Steam Game Name]:', game_name)

    if data.find(const.steam_text_owned) != -1:
        print('>>> Owned <<<')
        owned = True

    if data.find(const.steam_text_limited) != -1 or data.find(const.steam_text_learning) != -1:
        print('>>> Limited <<<')
        limited = True

    if data.find(const.steam_text_card) != -1:
        print('>>> Card <<<')
        card = True
        have_card = True
    else:
        print('>>> No Card <<<')

    if data.find(const.steam_text_dlc) != -1 or data.find(const.steam_text_soundtrack) != -1:
        print('>>> DLC <<<')
        is_dlc = True

    if data.find(const.steam_text_play) != -1 and soup.find(class_=const.steam_class_free).get_text(strip=True) == const.steam_text_free:
        print('>>> Free <<<')
        free = True

    must_card = configs.get_filter_config('must_have_card', False)
    must_free = configs.get_filter_config('must_not_free', False)

    return not owned and not limited and not is_dlc and (card or not must_card) and not (free and must_free)


def get_can_buy_from_steam_with_cache(url, headers, cookies, cache_info):
    """带多文件缓存的 get_can_buy_from_steam"""
    if url in cache_info:
        print(f'[CACHE] {url} -> False')
        return False

    try:
        result = get_can_buy_from_steam(url, headers, cookies)
        if result is False:
            cache_info[url] = False
        return result
    except Exception as e:
        if const.steam_err_lock in str(e):
            cache_info[url] = False
        print(f'[ERROR] {url}:', e)
        return False


if __name__ == '__main__':
    sort_key        = configs.get_base_config('sort_key', const.sort_key_discount)
    page_size       = configs.get_base_config('page_size', 0)
    loop_sleep_time = configs.get_base_config('loop_sleep_time', 0)

    max_price_display       = configs.get_filter_config('max_price_display', 0)
    max_price_real          = configs.get_filter_config('max_price_real', 0)
    max_discount_display    = configs.get_filter_config('max_discount_display', 0)
    max_discount_real       = configs.get_filter_config('max_discount_real', 0)
    must_have_card          = configs.get_filter_config('must_have_card', False)
    must_not_free           = configs.get_filter_config('must_not_free', False)

    max_budget      = configs.get_pay_config('max_budget', 0)
    max_order       = configs.get_pay_config('max_order', 0)
    confirm_pause   = configs.get_pay_config('confirm_pause', True)

    buy_list = []

    while True:
        next_loop = False
        cache       = util.load_cache(must_have_card, must_not_free)
        page_number = configs.get_base_config('page_number', 1)
        max_page    = configs.get_base_config('max_page', 1)

        try:
            while max_page != 0:
                print('\n[PAGE NUMBER]:', page_number)

                if not steam_api.is_game_owned(configs.get_base_config('verify_url', ''), ):
                    print('Steam Cookie Expired, Please Login')
                    exit(0)

                content = py_api.get_rank_list(page_number, page_size, sort_key)
                if len(content) == 0:
                    print('Py Cookie Expired, Please Login')
                    exit(0)

                cnt = 1
                page_number += 1
                max_page -= 1

                for info in content:
                    if py_api.total_price >= max_budget or py_api.total_order >= max_order:
                        print(f'[Out of Budget]: {py_api.total_price}r/{max_budget}r {py_api.total_order}/{max_order}')
                        util.save_cache(cache, must_have_card, must_not_free)
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
                        'py_price'      : util.get_json_value(info, ['keyTxAmt'], '999'),
                        'steam_price'   : util.get_json_value(info, ['oriPrice'], '999'),
                        'discount'      : util.get_json_value(info, ['keyDiscount'], '1'),
                    }

                    if get_can_buy_from_steam_with_cache(target_url, const.steam_headers, const.steam_cookies, cache):
                        util.print_buy_game(buy_game_info)
                        if float(buy_game_info['py_price']) > max_price_display:
                            print(f'[CDK Price] {buy_game_info['py_price']} > [Max Price] {max_price_display}')
                            if sort_key == const.sort_key_price:
                                next_loop = True
                                break
                        elif float(buy_game_info['discount']) > max_discount_display:
                            print(f'[CDK Discount] {buy_game_info['discount']} > [Max Discount] {max_discount_display}')
                            if sort_key == const.sort_key_discount:
                                next_loop = True
                                break
                        if configs.get_pay_config('auto_pay', False):
                            success, msg, order_price = py_api.pay_order(
                                game_id,
                                max_price_real,
                                max_discount_real,
                                buy_game_info['steam_price'],
                                confirm_pause,
                                have_card
                            )
                            if success:
                                buy_game_info['py_price'] = order_price
                                buy_game_info['discount'] = buy_game_info['py_price'] / float(buy_game_info['steam_price'])
                                buy_list.append(buy_game_info)
                                print(f'[Success]: {order_price}r')
                                if configs.get_email_config('auto_email', False):
                                    util.send_email(
                                        const.email_title,
                                        f'Name: {buy_game_info['name']}' +
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
                                print(f'[Failed]: {msg}')

                            if success or order_price > 0:
                                if configs.get_pay_config('pause_beep', False):
                                    util.beep()
                                if confirm_pause:
                                    input('>>> Press Enter to Continue: ')

                        else:
                            buy_list.append(buy_game_info)

                    print('=' * 10, f'{cnt}.', py_name, '=' * 10)
                    print()
                    cnt += 1

                util.print_buy_list(buy_list)

                if next_loop:
                    break

        finally:
            util.save_cache(cache, must_have_card, must_not_free)

        if loop_sleep_time > 0:
            print(f'>>> Loop End, Sleep {loop_sleep_time}s...\n')
            time.sleep(loop_sleep_time)
        else:
            break
