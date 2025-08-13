import pay
import time
import util
import const
import requests
from config import configs
from util import load_cache, save_cache, send_email


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
                headers=const.steam_headers,
                cookies=const.steam_cookies
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
