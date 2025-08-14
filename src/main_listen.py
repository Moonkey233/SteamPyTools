import time
import util
import const
import py_api
import steam_api
import threading
from config import configs


stop_event = threading.Event()


def listen_game(listen_id, listen_price):
    """监听一个游戏是否购买成功，如果没买则循环调用 pay_order"""
    pay_time = configs.get_pay_config('pay_time', 2000)

    while not stop_event.is_set():
        try:
            game_url, steam_price, game_name = py_api.get_info_by_id(listen_id)

            if steam_api.is_game_owned(game_url):
                print(f"[{game_name}] Already Owned, Exit Listening.")
                break

            ok = False
            while not ok and not stop_event.is_set():
                ok, msg, code = py_api.pay_order(
                    game_id         = listen_id,
                    max_price       = listen_price,
                    max_discount    = 1.0,
                    steam_price     = steam_price,
                    confirm_pause   = False
                )

                if ok:
                    if configs.get_pay_config('pause_beep', False):
                        util.beep()
                    print(f'[Success]: {code}r')
                    if configs.get_email_config('auto_email', False):
                        util.send_email(
                            const.email_title,
                            f'Name: {game_name}' +
                            f'\nPrice：{code}r' +
                            f'\nSteam：{steam_price}' +
                            f'\nLink：{game_url}' +
                            const.email_notify,
                            configs.get_email_config('email_addr', []),
                            configs.get_email_config('smtp_from', ''),
                            configs.get_email_config('smtp_server', ''),
                            configs.get_email_config('smtp_port', 0),
                            configs.get_email_config('smtp_pwd', '')
                        )

                if not ok:
                    if code == -2:
                        break
                    elif code == -1:
                        max_budget = configs.get_pay_config('max_budget', 0)
                        max_order = configs.get_pay_config('max_order', 0)
                        print(f'[Out of Budget]: {py_api.total_price}r/{max_budget}r {py_api.total_order}/{max_order}')
                        stop_event.set()
                        return
                    else:
                        continue

            if stop_event.is_set():
                break

            print(f"[{game_name}] Already Purchased, Cooling Down.")
            time.sleep(pay_time + 1)

        except Exception as e:
            print(f"[ERROR] {listen_id}: {e}")
            time.sleep(pay_time + 1)


if __name__ == "__main__":
    threads = []
    listen_list = configs.get_listen_config('listen_list', [])
    try:
        if not steam_api.is_game_owned(configs.get_base_config('verify_url', ''), ):
            print('Steam Cookie Expired, Please Login')
            exit(0)

        content = py_api.get_rank_list(1, 1, const.sort_key_discount)
        if len(content) == 0:
            print('Py Cookie Expired, Please Login')
            exit(0)

        for game_id, max_price in listen_list:
            t = threading.Thread(target=listen_game, args=(game_id, max_price))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    except KeyboardInterrupt:
        print("\n[EXIT] Ctrl+C detected, stopping all threads...")
        stop_event.set()
        for t in threads:
            t.join()
    finally:
        py_api.save_pay_map()
        input('[LISTEN] End Listening, Press Enter to Exit.')
