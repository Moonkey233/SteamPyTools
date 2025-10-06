# SteamPyTools

一个用于配合 steampy.com（Key/激活码平台）与 Steam 商店页进行筛选与自动下单的 Python 小工具集。支持两种使用方式：

- 扫描模式：分页抓取 steampy 热榜，结合 Steam 商品页信息做过滤，符合条件可自动下单；
- 监听模式：对给定的游戏 ID 与目标价持续监听，满足条件立即下单。

> 提示：仓库内 `src/py.curl` 与 `src/steam.curl` 是示例。实际运行请把你自己的 cURL 请求文件放到仓库根目录的 `curl/` 目录（已在 `.gitignore` 中忽略），以避免泄露隐私凭据。

## 目录结构

```
SteamPyTools/
├─ src/
│  ├─ main_scan.py        # 扫描模式入口
│  ├─ main_listen.py      # 监听模式入口（多线程）
│  ├─ config.py           # 运行配置（分页、过滤、支付、监听、邮件）
│  ├─ const.py            # 常量与路径、接口地址、cURL 解析
│  ├─ util.py             # 工具方法：缓存/邮件/beep/cURL 解析/打印
│  ├─ py_api.py           # steampy 接口：热榜/详情/出售信息/下单
│  ├─ steam_api.py        # Steam 页面判断：是否已拥有
│  ├─ py.curl             # 示例：steampy 的 cURL 请求（仅示例）
│  └─ steam.curl          # 示例：Steam 的 cURL 请求（仅示例）
├─ .gitignore             # 忽略 curl/ cache/ smtp/ 等敏感/临时目录
└─ (运行时目录)
   ├─ curl/               # 放置你自己的 py.curl 与 steam.curl（推荐位置）
   ├─ cache/              # 运行时缓存（自动生成）
   └─ smtp/               # SMTP 配置（可选）
```

## 环境要求

- 系统：建议 Windows（`winsound` 用于蜂鸣提示；非 Windows 可将 `pause_beep=False` 关闭蜂鸣）
- Python：3.8+（建议 3.10/3.11）
- 依赖：`requests`、`urllib3`、`beautifulsoup4`

安装依赖示例：

```bash
pip install -U requests urllib3 beautifulsoup4
```

## 准备工作（Cookies / cURL）

程序通过解析 cURL 文件获取请求头与 Cookies，请先在浏览器中登录：

1) steampy 平台（https://steampy.com）
2) Steam 商店（https://store.steampowered.com）

然后：
- 使用浏览器的“复制为 cURL”功能，分别复制 steampy 与 Steam 的请求；
- 将内容保存为两份文件：`curl/py.curl` 与 `curl/steam.curl`（推荐放在仓库根目录的 `curl/` 目录）；
- 文件中需包含 `-H`（headers）与 `-b`（cookies）等参数，示例可参考 `src/py.curl` 与 `src/steam.curl`；
- `const.py` 会从 `../curl/py.curl` 和 `../curl/steam.curl` 读取配置（相对 `src/` 目录）。

安全提醒：`curl/` 目录已在 `.gitignore` 中忽略，请不要提交真实 Token/Cookie 到仓库。

## 使用方式

- 扫描模式（批量筛选 + 可自动下单）

  ```bash
  python src/main_scan.py
  ```

  功能概览：
  - 分页拉取 steampy 热榜；
  - 把每个条目对应的 Steam 商品页拉取并解析，判断：是否已拥有、是否限地区/学习版、是否 DLC/原声集、是否有卡牌、是否免费等；
  - 按价格与折扣阈值过滤；
  - `auto_pay=True` 时自动下单（支持预算/数量/冷却等管控）；
  - 支持循环执行（`loop_sleep_time>0`）。

- 监听模式（盯盘 + 即时下单）

  ```bash
  python src/main_listen.py
  ```

  功能概览：
  - 从 `config.py` 的 `listen_list` 读取 (game_id, max_price) 列表；
  - 为每个监听项启动线程，持续轮询 steampy 出售信息，满足价格即可下单；
  - 遵循预算/数量上限与冷却时间设置。

## 配置说明（`src/config.py`）

核心配置分为五组，通过 `Config` 单例访问：

- base_config：分页/排序/循环
  - `verify_url`：用于校验 Steam Cookie 是否有效的任意商品页；
  - `page_number`/`max_page`/`page_size`：拉取热榜的分页参数；
  - `loop_sleep_time`：循环间隔（秒），<=0 表示只跑一轮；
  - `sort_key`：`const.sort_key_discount` 或 `const.sort_key_price`。

- filter_config：过滤条件
  - `max_price_display`/`max_discount_display`：列表展示价格/折扣的阈值（粗筛）；
  - `max_price_real`/`max_discount_real`：实际下单价格/折扣阈值（严筛）；
  - `must_have_card`：是否必须带卡牌；
  - `must_not_free`：是否排除免费。

- pay_config：自动支付与风控
  - `auto_pay`：是否自动下单；
  - `use_balance`：是否使用余额（设置后会添加 `walletFlag`）；
  - `confirm_pause`：下单前是否人工确认；
  - `pause_beep`：提示蜂鸣（Windows 有效）；
  - `max_budget`/`max_order`：本次会话累计预算与下单数上限；
  - `list_size`：取前多少个在售订单尝试；
  - `pay_time`：对同一游戏的冷却时间（秒），避免重复下单；
  - `promo_code_id`/`pay_type`：优惠券与支付方式。

- listen_config：监听列表
  - `listen_list=[(game_id, max_price), ...]`。

- email_config：邮件通知（可选）
  - `auto_email=True` 时生效；
  - 可在 `smtp/smtp_config.txt` 提供 4 行配置：`server`、`port`、`from`、`password`；
  - 或直接在 `config.py` 中填充。

## 运行时文件与缓存

- `cache/`：
  - `cache_{must_have_card}_{must_not_free}.json`：Steam 可购买性判定缓存；
  - `pay_map.json`：下单冷却与简单去重（由 `py_api` 读写）。
- `smtp/smtp_config.txt`：当 `auto_email=True` 时读取，四行依次为：服务器、端口、发件人、授权码/密码。

## 已知说明与限制

- cURL 路径：代码默认从仓库根目录的 `curl/` 读取。`src/` 下的示例仅供参考，实际运行请把你自己的文件放到 `curl/`。
- 平台与语言：`winsound` 为 Windows 专用，非 Windows 系统请将 `pause_beep=False`；
- 风险提示：自动下单存在风险，请谨慎设置预算与确认逻辑，确保遵循平台条款；
- 隐私安全：请勿将 `curl/` 与任何含有 Token/Cookie 的文件提交到仓库。

## 常见错误排查

- “Steam Cookie Expired, Please Login”：Steam 登录态失效，请重新复制最新 `steam.curl`；
- “Py Cookie Expired, Please Login”：steampy 登录态失效，重新复制最新 `py.curl`；
- 403/401：通常为 Cookie/Token 过期或缺少必要 Header；
- `NoneType has no attribute get_text`：Steam 页结构异常或被限制，稍后重试。

## 版权与声明

本工具仅用于学习与研究，请自行承担使用风险；请遵守相关网站/平台的服务条款与法律法规。

