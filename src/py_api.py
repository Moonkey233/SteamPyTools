import os
import time
import json
import util
import const
import atexit
import requests
import threading
from config import configs


pay_map     = {}
total_price = 0
total_order = 0
pay_lock    = threading.Lock()


def load_pay_map():
    """启动时加载缓存"""
    global pay_map
    if os.path.exists(const.pay_map_path):
        try:
            with open(const.pay_map_path, 'r', encoding='utf-8') as f:
                pay_map = json.load(f)
            print(f'[CACHE LOADED] {len(pay_map)} entries from {const.pay_map_path}')
        except Exception as e:
            print(f'[CACHE LOAD ERROR] {e}')
            pay_map = {}
    else:
        pay_map = {}


def save_pay_map():
    """退出时保存缓存"""
    try:
        dir_path = os.path.dirname(const.pay_map_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with open(const.pay_map_path, 'w', encoding='utf-8') as f:
            json.dump(pay_map, f, ensure_ascii=False, indent=2)
        print(f'[CACHE SAVED] {len(pay_map)} entries to {const.pay_map_path}')
    except Exception as e:
        print(f'[CACHE SAVE ERROR] {e}')


load_pay_map()
atexit.register(save_pay_map)


def get_list_sale(game_id):
    """根据gameID获取订单列表"""
    time.sleep(0.5)
    list_sale_query = {
        'pageNumber': 1,
        'pageSize'  : configs.get_pay_config('list_size', 0),
        'sort'      : 'keyPrice',
        'order'     : 'asc',
        'startDate' : '',
        'endDate'   : '',
        'gameId'    : game_id,
    }

    try:
        resp = requests.get(
            url     = const.py_list_sale_url,
            params  = list_sale_query,
            headers = const.py_headers,
            cookies = const.py_cookies
        ).json()
        return util.get_json_value(resp, ['result', 'content'], [])
    except Exception as err:
        print(f'[ERROR]: {err}')
        return []


def pay_order(game_id, max_price, max_discount, steam_price, confirm_pause=True, have_card=False):
    """根据游戏id发起最优符合条件的支付请求，不符合条件不支付"""
    global total_price, total_order, pay_map

    max_budget      = configs.get_pay_config('max_budget', 0)
    max_order       = configs.get_pay_config('max_order', 0)
    pay_type        = configs.get_pay_config('pay_type', 'AL')
    promo_code_id   = configs.get_pay_config('promo_code_id', '')
    use_balance     = configs.get_pay_config('use_balance', False)
    sort_key        = configs.get_base_config('sort_key', const.sort_key_discount)
    card_price      = configs.get_filter_config('card_price', 0)
    data = {
        'payType': pay_type,
        'promoCodeId': promo_code_id,
    }
    if use_balance:
        data['walletFlag'] = 'useBalance'

    # 加读锁
    with pay_lock:
        # 一个game_id只有一个线程，pay_map读安全，优先用时间筛掉重复支付
        if game_id in pay_map and pay_map[game_id] > time.time():
            time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(pay_map[game_id]))
            return False, f'Already paid for {game_id}, will not repay until {time_str}', -2

        # 预算判定
        if total_price >= max_budget or total_order >= max_order:
            return False, f'Out of Budget: {total_price}r/{max_budget}r {total_order}/{max_order}', -1

    # 最耗时的一步，不加锁
    order_list = get_list_sale(game_id)

    # 加锁操作，较少订单会进入post，post调用较少，因此post一起锁住保证一致性
    with pay_lock:
        for order in order_list:
            key_price = float(util.get_json_value(order, 'keyPrice', '999'))
            real_discount = key_price / float(steam_price)
            print(f'\n[Game ID]: {game_id} [Real Price]: {key_price:.2f} [Real Discount]: {real_discount:.4f}')

            # 绝大多数在此返回，再次精确判定预算，有卡额外减去卡牌金额计算
            if total_price + key_price > max_budget:
                return False, 'No Orders Meet the Filter', 0
            if sort_key == const.sort_key_discount and have_card:
                key_price -= card_price
                real_discount = key_price / float(steam_price)
                print(f'[After Card Price]: {key_price:.2f} [After Card Discount]: {real_discount:.4f}')
            if key_price > max_price or real_discount > max_discount:
                return False, 'No Orders Meet the Filter', 0

            if configs.get_pay_config('pause_beep', False):
                util.beep()

            if confirm_pause:
                if input('<<< ----------!!![IMPORTANT]!!!---------- >>> Press Input [N/n] to Cancel: ').strip().lower() == 'n':
                    return False, 'Canceled by User', 1

            data['saleId'] = util.get_json_value(order, 'saleId', '')

            pay_resp = requests.post(
                url     = const.py_pay_order_url,
                headers = const.py_headers,
                cookies = const.py_cookies,
                data    = data
            )
            pay_data = pay_resp.json()

            print(pay_data)

            if (pay_resp.status_code == 200 and
                    util.get_json_value(pay_data, ['message'], '') == 'success' and
                    util.get_json_value(pay_data, ['success'], False)):
                pay_price = float(util.get_json_value(pay_data, ['result', 'payPrice'], '999'))

                # 写入预算
                total_price += key_price
                total_order += 1
                pay_map[game_id] = time.time() + configs.get_pay_config('pay_time', 2000)

                return True, util.get_json_value(pay_data, ['result', 'orderId'], ''), pay_price


    return False, 'No Orders Meet the Filter', 2


def get_rank_list(page_number=1, page_size=30, sort_key=const.sort_key_discount):
    """获取排行榜单"""
    try:
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
        ).json()

        content = util.get_json_value(py_resp, ['result', 'content'], [])
        if content is None or len(content) == 0:
            return []
        return content
    except Exception as err:
        print(f'[ERROR]: {err}')
        return []


def get_info_by_id(game_id):
    """根据py game_id 获取 Steam 链接和原价"""
    try:
        get_one_query = {
            'gameId': game_id,
        }

        py_resp = requests.get(
            url     = const.py_get_one_url,
            params  = get_one_query,
            headers = const.py_headers,
            cookies = const.py_cookies
        ).json()

        gama_url    = util.get_json_value(py_resp, ['result', 'gameUrl'], '')
        steam_price = util.get_json_value(py_resp, ['result', 'oriPrice'], 999)
        py_name     = util.get_json_value(py_resp, ['result', 'gameNameCn'], '')
        if py_name == '' or py_name is None:
            py_name = util.get_json_value(py_resp, ['result', 'gameName'], '')
        return gama_url, steam_price, py_name
    except Exception as err:
        print(f'[ERROR]: {err}')
        return '', 999, ''
