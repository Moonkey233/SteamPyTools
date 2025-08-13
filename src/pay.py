import time
import util
import const
import requests
import list_sale
import threading
from config import configs


total_price = 0
total_order = 0
pay_map     = {}
pay_lock    = threading.Lock()

def pay_order(game_id, max_price, max_discount, steam_price, confirm_pause=True):
    """根据游戏id发起最优符合条件的支付请求，不符合条件不支付"""
    global total_price, total_order, pay_map

    max_budget = configs.get_pay_config('max_budget', 0)
    max_order = configs.get_pay_config('max_order', 0)
    pay_type = configs.get_pay_config('pay_type', 'AL')
    promo_code_id = configs.get_pay_config('promo_code_id', '')
    use_balance = configs.get_pay_config('use_balance', False)
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
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(pay_map[game_id]))
            return False, f'Already paid for {game_id}, will not repay until {time_str}', -2

        # 粗估计，筛掉一部分
        if total_price >= max_budget or total_order >= max_order:
            return False, f'Out of Budget: {total_price}r/{max_budget}r {total_order}/{max_order}', -1

    # 最耗时的一步，不加锁
    order_list = list_sale.get_list_sale(game_id)

    # 加锁操作，较少订单会进入post，post调用较少，因此post一起锁住保证一致性
    with pay_lock:
        for order in order_list:
            key_price = float(util.get_json_value(order, 'keyPrice', ''))
            real_discount = key_price / float(steam_price)
            print(f'[Real Price]: {key_price}, [Real Discount]: {real_discount:.4f}')

            # 绝大多数在此返回
            if key_price > max_price or real_discount > max_discount:
                break

            # 再次精确判定预算
            if total_price + key_price > max_budget:
                break

            data['saleId'] = util.get_json_value(order, 'saleId', '')

            if confirm_pause:
                if configs.get_pay_config('pause_beep', False):
                    util.beep()
                if input('<<< ----------!!![IMPORTANT]!!!---------- >>> Press Input [N/n] to Cancel: ').lower() == 'n':
                    return False, 'Canceled by User', 0

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
                pay_price = float(util.get_json_value(pay_data, ['result', 'payPrice'], ''))

                # 写入预算
                total_price += key_price
                total_order += 1
                pay_map[game_id] = time.time() + configs.get_pay_config('pay_time', 2000)

                return True, util.get_json_value(pay_data, ['result', 'orderId'], ''), pay_price


    return False, 'No Orders Meet the Filter', 0
