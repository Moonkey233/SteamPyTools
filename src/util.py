import os
import json
import shlex
import smtplib
import winsound
from email.header import Header
from email.mime.text import MIMEText


def get_cache_file_path(must_have_card, must_not_free):
    """根据参数组合生成缓存文件路径"""
    cache_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../cache/'))
    return os.path.join(cache_path, f'cache_{must_have_card}_{must_not_free}.json')


def load_cache(must_have_card, must_not_free):
    """加载指定参数组合的缓存"""
    file_path = get_cache_file_path(must_have_card, must_not_free)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as err:
            print(f'[LOAD ERROR] {file_path}: {err}')
            return {}
    return {}


def save_cache(cacheInfo, must_have_card, must_not_free):
    """保存指定参数组合的缓存"""
    file_path = get_cache_file_path(must_have_card, must_not_free)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(cacheInfo, f, ensure_ascii=False, indent=2)


def parse_curl_file(file_path):
    """解析curl(bash)文件 为用户 headers & cookies"""
    with open(file_path, 'r', encoding='utf-8') as f:
        curl_str = f.read()

    parts = shlex.split(curl_str)

    headers = {}
    cookies = {}

    i = 0
    while i < len(parts):
        if parts[i] == '-H':
            header_str = parts[i + 1]
            if ':' in header_str:
                k, v = header_str.split(':', 1)
                headers[k.strip()] = v.strip()
            else:
                headers[header_str.strip()] = ''
            i += 2
        elif parts[i] == '-b':
            cookie_str = parts[i + 1]
            for c in cookie_str.split(';'):
                if '=' in c:
                    k, v = c.split('=', 1)
                    cookies[k.strip()] = v.strip()
            i += 2
        else:
            i += 1

    return headers, cookies


def send_email(title, content, email_addr, smtp_from, smtp_server, smtp_port, smtp_pwd):
    """发送邮件"""
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = Header(smtp_from)
    msg['To'] = Header(','.join(email_addr))
    msg['Subject'] = Header(title, 'utf-8')

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(smtp_from, smtp_pwd)
        server.sendmail(smtp_from, email_addr, msg.as_string())
        server.quit()
        print('Send Email Successfully')
    except Exception as e:
        print('Send Email Error：', e)


def get_json_value(data, path, default=None):
    """从嵌套 JSON 里安全获取值, 找不到时返回的默认值"""
    if isinstance(path, str):
        path = path.strip('.').split('.')

    try:
        for key in path:
            if isinstance(data, dict):
                data = data.get(key, default)
            elif isinstance(data, list):
                try:
                    idx = int(key)
                    data = data[idx]
                except (ValueError, IndexError):
                    return default
            else:
                return default
            if data is default:
                return default
        return data
    except Exception as err:
        print(f'[ERROR]:', err)
        return default


def print_buy_game(game):
    """格式化输出游戏"""
    print(
        'Name:', game['name'],
        'CDK:', game['py_price'],
        'Steam:', game['steam_price'],
        'Discount:', game['discount'],
        game['steam'], game['py']
    )


def print_buy_list(game_list):
    """格式化输出已购买列表"""
    print()
    print('=' * 20, 'Buy List', '=' * 20)
    print(f'Total: {len(game_list)}')

    for game in game_list:
        print_buy_game(game)

    print('=' * 20, 'Buy List', '=' * 20)
    print()


def beep(frequency=500, duration=500, times=2):
    """调用蜂鸣器发声"""
    for i in range(times):
        winsound.Beep(frequency, duration)
