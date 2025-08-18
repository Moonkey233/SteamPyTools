import util
import const


# ==================== 基本设置 ====================
verify_url      = 'https://store.steampowered.com/app/504230'   # Celeste蔚蓝，这里选一个Steam库里有的游戏，用于验证Cookie是否过期
page_number     = 1                                             # 从py的第几页开始抓取
max_page        = 300                                           # 一共抓取py前多少页
page_size       = 50                                            # 每一页的大小
loop_sleep_time = 600                                           # 循环检测间隔时间，单位：秒，<=0时只执行一次
sort_key        = const.sort_key_discount                       # sort_key_discount 折扣(一般用于加库存价值) / sort_key_price 价格(一般用于挂卡控制成本)
# ==================== 基本设置 ====================


# ==================== 监听模式设置 ====================
listen_list = [
    (768560289619644416, 50),   # 生化危机4重制黄金版
    (760680624183840768, 20),   # 幻兽帕鲁
    (811661096296386560, 99),   # 黑神话：悟空
    (575406630020059136, 50),   # 霍格沃兹之遗
]
# ==================== 监听模式设置 ====================


# ==================== 扫描模式过滤器 ====================
max_price       = 10        # 接受的最大CDK价格，实际价格比该数字高则不计入，单位：元，支持小数，仅扫描模式
max_discount    = 0.031     # 接受的最高折扣，实际折扣比该数字高则不计入，0.05指 -95% off，仅扫描模式
must_have_card  = False     # 是否必须有卡，False则只判断是否已入库、是否资料受限，仅扫描模式
must_not_free   = True      # 是否排除免费游戏，False则符合条件的免费游戏也会可购买，仅扫描模式
# ==================== 扫描模式过滤器 ====================


# ==================== 自动支付 ====================
auto_pay         = True      # 是否启用自动支付，监听模式始终自动支付
use_balance      = True      # 是否使用余额支付
confirm_pause    = True      # 是否确认支付暂停，监听模式不可用
pause_beep       = True      # 暂停是否调用蜂鸣器
max_budget       = 300       # 最大预算，单位：CNY，可为小数，下单总金额不会超过该值
max_order        = 100       # 最大订单数，下单总数不会超过该值
list_size        = 2         # 获取前多少个订单
pay_time         = 2000      # 成功购买某一个游戏后 pay_time 秒内不再重复下单
promo_code_id    = ''        # 优惠券id，默认为空
pay_type         = 'AL'      # 支付方式，只能为AL
# ==================== 自动支付 ====================


# ==================== 邮件设置 ====================
auto_email  = False                         # 是否启用邮件通知，若启用，请配置smtp
email_addr  = ['Moonkey233@foxmail.com']    # 收件人列表
smtp_server = ''                            # smtp服务器
smtp_port   = 0                             # smtp端口
smtp_from   = ''                            # smtp寄件人
smtp_pwd    = ''                            # smtp授权码
if auto_email:
    try:
        with open(const.smtp_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]
            if len(lines) >= 4:
                smtp_server = lines[0]
                smtp_port   = int(lines[1])
                smtp_from   = lines[2]
                smtp_pwd    = lines[3]
            else:
                print('Invalid smtp_config.txt, use code config')
    except Exception as err:
        print('Invalid smtp_config.txt, use code config, err:', err)
# ==================== 邮件设置 ====================


# ======================================== 配置部分END ========================================


base_config = {
    'verify_url'        : verify_url,
    'page_number'       : page_number,
    'max_page'          : max_page,
    'page_size'         : page_size,
    'loop_sleep_time'   : loop_sleep_time,
    'sort_key'          : sort_key,
}

listen_config = {
    'listen_list'   : listen_list,
}

filter_config = {
    'max_price'     : max_price,
    'max_discount'  : max_discount,
    'must_have_card': must_have_card,
    'must_not_free' : must_not_free,
}

pay_config = {
    'auto_pay'      : auto_pay,
    'use_balance'   : use_balance,
    'confirm_pause' : confirm_pause,
    'pause_beep'    : pause_beep,
    'max_budget'    : max_budget,
    'max_order'     : max_order,
    'list_size'     : list_size,
    'pay_time'      : pay_time,
    'promo_code_id' : promo_code_id,
    'pay_type'      : pay_type,
}

email_config = {
    'auto_email'    : auto_email,
    'smtp_server'   : smtp_server,
    'smtp_port'     : smtp_port,
    'smtp_from'     : smtp_from,
    'smtp_pwd'      : smtp_pwd,
    'email_addr'    : email_addr,
}

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.base_config = base_config
            cls._instance.listen_config = listen_config
            cls._instance.filter_config = filter_config
            cls._instance.pay_config = pay_config
            cls._instance.email_config = email_config
        return cls._instance

    def get_base_config(self, key, default=None):
        return util.get_json_value(self.base_config, key, default)

    def get_listen_config(self, key, default=None):
        return util.get_json_value(self.listen_config, key, default)

    def get_filter_config(self, key, default=None):
        return util.get_json_value(self.filter_config, key, default)

    def get_pay_config(self, key, default=None):
        return util.get_json_value(self.pay_config, key, default)

    def get_email_config(self, key, default=None):
        return util.get_json_value(self.email_config, key, default)

configs = Config()
