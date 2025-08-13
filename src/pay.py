import util
import const
import requests
import list_sale
from config import configs


totalPrice = 0
totalOrder = 0

def pay_order(gameID, price, discount, steam_price):
    """根据游戏id发起最优符合条件的支付请求，不符合条件不支付"""
    global totalPrice, totalOrder

    max_budget = configs.get_pay_config('max_budget', 0)
    max_order = configs.get_pay_config('max_order', 0)
    pay_type = configs.get_pay_config('pay_type', 'AL')
    promo_code_id = configs.get_pay_config('promo_code_id', '')
    use_balance = configs.get_pay_config('use_balance', False)
    confirm_pause = configs.get_pay_config('confirm_pause', True)

    if totalPrice >= max_budget or totalOrder >= max_order:
        return False, f'Out of Budget: {totalPrice}r/{max_budget}r {totalOrder}/{max_order}', -1

    data = {
        'payType':      pay_type,
        'promoCodeId':  promo_code_id,
    }

    if use_balance:
        data['walletFlag'] = 'useBalance'

    for order in list_sale.get_list_sale(gameID):
        key_price = float(util.get_json_value(order, 'keyPrice'))
        real_discount = key_price / float(steam_price)

        if (key_price > price or
                real_discount > discount or
                totalPrice + key_price > max_budget):
            break

        data['saleId'] = util.get_json_value(order, 'saleId', '')

        print(f'Real Price: {key_price}, Real Discount: {real_discount:.2f}')
        if confirm_pause:
            input('Press Enter to Continue: ')

        payResp = requests.post(
            url=const.py_pay_order_url,
            headers=const.py_headers,
            cookies=const.py_cookies,
            data=data
        )
        payData = payResp.json()

        if (payResp.status_code == 200 and
                util.get_json_value(payData, ['message'], '') == 'success' and
                util.get_json_value(payData, ['success'], False)):
            pay_price = util.get_json_value(payData, ['result', 'payPrice'], '')
            totalPrice += float(pay_price)
            totalOrder += 1
            return True, util.get_json_value(payData, ['result', 'orderId'], ''), float(pay_price)

    return False, 'no orders meet the filter', 0
