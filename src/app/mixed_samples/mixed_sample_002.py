# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2129_lm, name=begin) ===
async def begin(request: web.Request) -> web.Response:
    """ Begin a session
    """
    session = await request.app['session_manager'].begin_session()
    session_id = session.id
    response = web.Response(text=session_id)
    response.set_cookie(SESSION_COOKIE_NAME, session_id)
    return response

# === BLOCK 2 (label=lm, source_idx=line2567_lm, name=list_share_single_file) ===
def list_share_single_file(cookie, tokens, uk, shareid):
    """获取单独共享出来的文件.

    目前支持的链接格式有:
      * http://pan.baidu.com/wap/link?uk=202032639&shareid=420754&third=0
      * http://pan.baidu.com/share/link?uk=202032639&shareid=420754
    """
    if not isinstance(cookie, dict):
        raise TypeError("cookie must be a dict")
    if not isinstance(tokens, str):
        raise TypeError("tokens must be a str")
    if not isinstance(uk, str):
        raise TypeError("uk must be a str")
    if not isinstance(shareid, str):
        raise TypeError("shareid must be a str")
    if not re.match(r"^\d+$", uk):
        raise ValueError("uk must be a number")
    if not re.match(r"^\d+$", shareid):
        raise ValueError("shareid must be a number")
    url = f"https://pan.baidu.com/share/list?uk={uk}&shareid={shareid}"
    headers = {
        "Cookie": "; ".join([f"{k}={v}" for k, v in cookie.items()]),
        "User-Agent": "netdisk;4.6.0.9;PC;PC-Windows;10.0.17763;WindowsBaiduYunGuanJia",
    }
    response = requests.get(url, headers=headers, params={"channel": "chunlei", "web": "1", "app_id": "250528"})
    response.raise_for_status()
    data = response.json()
    if data["errno"]!= 0:
        raise Exception(f"Failed to get share list: {data['errno']}")
    return data["list"]

# === BLOCK 3 (label=lm, source_idx=line267_lm, name=run) ===
def run(self):
        """Run the example consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the SelectConnection to operate.

        """
        self.connect()
        self.channel.basic_consume(self.on_message, queue=self.queue_name)
        self.channel.start_consuming()

# === BLOCK 4 (label=human, source_idx=line1488_human, name=make_signed_token) ===
def make_signed_token(self, key):
        """Signs the payload.

        Creates a JWS token with the header as the JWS protected header and
        the claims as the payload. See (:class:`jwcrypto.jws.JWS`) for
        details on the exceptions that may be reaised.

        :param key: A (:class:`jwcrypto.jwk.JWK`) key.
        """

        t = JWS(self.claims)
        t.add_signature(key, protected=self.header)
        self.token = t
