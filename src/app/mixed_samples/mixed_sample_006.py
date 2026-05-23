# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line174_lm, name=exec_container_commands) ===
def exec_container_commands(self, action, c_name, **kwargs):
        """
        Runs all configured commands of a container configuration inside the container instance.

        :param action: Action configuration.
        :type action: dockermap.map.runner.ActionConfig
        :param c_name: Container name.
        :type c_name: unicode | str
        :return: List of exec command return values (e.g. containing the command id), if applicable, or ``None``
          if either no commands have been run or no values have been returned from the API.
        :rtype: list[dict] | NoneType
        """
        exec_results = []
        for command in action.commands:
            exec_result = self.client.exec_create(c_name, command, **kwargs)
            exec_results.append(exec_result)
        if exec_results:
            return exec_results
        else:
            return None

# === BLOCK 2 (label=lm, source_idx=line901_lm, name=complete_experiment) ===
def complete_experiment(self, status):
        """Record worker completion status to the experiment server.

        This is done using a GET request to the /worker_complete
        or /worker_failed endpoints.
        """
        if status == "completed":
            self.experiment_server.worker_complete()
        elif status == "failed":
            self.experiment_server.worker_failed()
        else:
            raise ValueError("Invalid status")

# === BLOCK 3 (label=human, source_idx=line1593_human, name=sync_user) ===
def sync_user(self, url, token, encoding_aes_key, media_id, to_invite=True):
        """
        增量更新成员

        https://work.weixin.qq.com/api/doc#90000/90135/90980

        :param url: 企业应用接收企业微信推送请求的访问协议和地址，支持http或https协议
        :param token: 用于生成签名
        :param encoding_aes_key: 用于消息体的加密，是AES密钥的Base64编码
        :param media_id: 上传的csv文件的media_id
        :param to_invite: 是否邀请新建的成员使用企业微信（将通过微信服务通知或短信或邮件下发邀请，每天自动下发一次，最多持续3个工作日），默认值为true。
        :return: 返回的 JSON 数据包
        """
        return self._post(
            'batch/syncuser',
            data={
                'media_id': media_id,
                'to_invite': to_invite,
                'callback': {
                    'url': url,
                    'token': token,
                    'encodingaeskey': encoding_aes_key
                }
            }
        )

# === BLOCK 4 (label=human, source_idx=line606_human, name=_add_left) ===
def _add_left(self, d):
        """
        Adds the provided domino to the left end of the board.

        :param Domino d: domino to add
        :return: None
        :raises EndsMismatchException: if the values do not match
        """
        if not self:
            self._left = d.first
            self._right = d.second
        elif d.second == self.left_end():
            self._left = d.first
        elif d.first == self.left_end():
            self._left = d.second
        else:
            raise dominoes.EndsMismatchException(
                '{} cannot be added to the left of'
                ' the board - values do not match!'.format(d)
            )

        self._length += 1

# === BLOCK 5 (label=human, source_idx=line2957_human, name=urlnext) ===
def urlnext(parser, token):
    """
    {% url %} copied from Django 1.7.
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError(
            "'%s' takes at least one argument"
            " (path to a view)" % bits[0]
        )
    viewname = parser.compile_filter(bits[1])
    args = []
    kwargs = {}
    asvar = None
    bits = bits[2:]
    if len(bits) >= 2 and bits[-2] == "as":
        asvar = bits[-1]
        bits = bits[:-2]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to url tag")
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))

    return URLNextNode(viewname, args, kwargs, asvar)

# === BLOCK 6 (label=lm, source_idx=line2528_lm, name=load_actions) ===
def load_actions(spec, group=None, expr_parser=None):
    """Each item can be an action name as a string or a dict. When using a dict,
    one key/item pair must be the action name and its options and the rest action
    decorator names and their options.
    Example:
        load_actions(["login_required", {"flash": {"message": "hello world", "label": "warning"}}])
    """
    actions = []
    for item in spec:
        if isinstance(item, str):
            actions.append(item)
        elif isinstance(item, dict):
            action_name, action_options = next(iter(item.items()))
            actions.append(action_name)
            for decorator_name, decorator_options in item[action_name].items():
                actions.append(decorator_name)
    return actions
