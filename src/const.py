import os
import util

email_title     = 'CDK下单成功通知'
email_notify    = '\n请及时支付登录兑换'

steam_text_owned        = '在库中'
steam_text_play         = '开始游戏'
steam_text_free         = '免费开玩'
steam_text_card         = '集换式卡牌'
steam_text_limited      = '个人资料功能受限'
steam_text_learning     = '正在了解该游戏'
steam_text_soundtrack   = '不包含基础游戏'
steam_text_dlc          = '此内容需要在 Steam 上拥有基础游戏'

steam_id_name       = 'appHubAppName'
steam_class_free    = 'game_purchase_price price'
steam_err_lock      = "'NoneType' object has no attribute 'get_text'"

sort_key_price      = 'keyPrice'
sort_key_discount   = 'keyDiscount'

py_rank_url         = 'https://steampy.com/xboot/steamGame/keyHot'
py_list_sale_url    = 'https://steampy.com/xboot/steamKeySale/listSale'
py_pay_order_url    = 'https://steampy.com/xboot/steamKeyOrder/payOrder'
py_detail_url       = 'https://steampy.com/cdkDetail?name=cn&gameId='
py_get_one_url      = 'https://steampy.com/xboot/steamGame/getOne'

base_dir                        = os.path.dirname(__file__)
file_path                       = os.path.abspath(os.path.join(base_dir, '../curl/py.curl'))
py_headers, py_cookies          = util.parse_curl_file(file_path)
file_path                       = os.path.abspath(os.path.join(base_dir, '../curl/steam.curl'))
steam_headers, steam_cookies    = util.parse_curl_file(file_path)
cache_path                      = os.path.abspath(os.path.join(base_dir, '../cache/'))
smtp_path                       = os.path.abspath(os.path.join(base_dir, '../smtp/smtp_config.txt'))
pay_map_path                    = os.path.abspath(os.path.join(base_dir, '../cache/pay_map.json'))
