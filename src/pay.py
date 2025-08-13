import util
import const
import requests
import list_sale
from config import configs


total_price = 0
total_order = 0

def pay_order(game_id, price, discount, steam_price):
    """根据游戏id发起最优符合条件的支付请求，不符合条件不支付"""
    global total_price, total_order

    max_budget = configs.get_pay_config('max_budget', 0)
    max_order = configs.get_pay_config('max_order', 0)
    pay_type = configs.get_pay_config('pay_type', 'AL')
    promo_code_id = configs.get_pay_config('promo_code_id', '')
    use_balance = configs.get_pay_config('use_balance', False)
    confirm_pause = configs.get_pay_config('confirm_pause', True)

    if total_price >= max_budget or total_order >= max_order:
        return False, f'Out of Budget: {total_price}r/{max_budget}r {total_order}/{max_order}', -1

    data = {
        'payType':      pay_type,
        'promoCodeId':  promo_code_id,
    }

    if use_balance:
        data['walletFlag'] = 'useBalance'

    for order in list_sale.get_list_sale(game_id):
        key_price = float(util.get_json_value(order, 'keyPrice', ''))
        real_discount = key_price / float(steam_price)

        if (key_price > price or
                real_discount > discount or
                total_price + key_price > max_budget):
            break

        data['saleId'] = util.get_json_value(order, 'saleId', '')

        print(f'[Real Price]: {key_price}, [Real Discount]: {real_discount:.2f}')
        if confirm_pause:
            if configs.get_pay_config('pause_beep', False):
                util.beep()
            input('Press Enter to Continue: ')

        payResp = requests.post(
            url=const.py_pay_order_url,
            headers=const.py_headers,
            cookies=const.py_cookies,
            data=data
        )
        pay_data = payResp.json()

        if (payResp.status_code == 200 and
                util.get_json_value(pay_data, ['message'], '') == 'success' and
                util.get_json_value(pay_data, ['success'], False)):
            pay_price = float(util.get_json_value(pay_data, ['result', 'payPrice'], ''))
            total_price += pay_price
            total_order += 1
            return True, util.get_json_value(pay_data, ['result', 'orderId'], ''), pay_price

    return False, 'No Orders Meet the Filter', 0
