import util
import const
import requests
from config import configs


def get_list_sale(game_id):
    """根据gameID获取订单列表"""
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
