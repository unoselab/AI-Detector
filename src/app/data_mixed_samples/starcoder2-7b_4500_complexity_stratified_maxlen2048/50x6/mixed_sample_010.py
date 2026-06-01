# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3530_lm, name=command) ===
def command(settings_module,
            command,
            bin_env=None,
            pythonpath=None,
            env=None,
            runas=None,
            *args, **kwargs):
    """
    Run arbitrary django management command

    CLI Example:

    .. code-block:: bash

        salt '*' django.command <settings_module> <command>
    """
    if not bin_env:
        bin_env = settings_module.split('.')

    if not pythonpath:
        pythonpath = [os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))]

    if not env:
        env = {}

    if not runas:
        runas = __opts__['user']

    cmd = [bin_env[0], bin_env[1], command] + list(args)

    return __salt__['cmd.run_all'](cmd, pythonpath=pythonpath, env=env, runas=runas, **kwargs)

# === BLOCK 2 (label=lm, source_idx=line4184_lm, name=_get_stack_frame) ===
def _get_stack_frame(stacklevel):
    """
    utility functions to get a stackframe, skipping internal frames.
    """
    frame = inspect.currentframe()
    for _ in range(stacklevel):
        frame = frame.f_back
    return frame

# === BLOCK 3 (label=lm, source_idx=line3209_lm, name=is_seq) ===
def is_seq(obj):
    """
    Check if an object is a sequence.
    """
    return isinstance(obj, (list, tuple, np.ndarray))

# === BLOCK 4 (label=human, source_idx=line793_human, name=update_cursor_position) ===
def update_cursor_position(self, line, index):
        """Update cursor position."""
        value = 'Line {}, Col {}'.format(line + 1, index + 1)
        self.set_value(value)

# === BLOCK 5 (label=human, source_idx=line1225_human, name=cached) ===
def cached(key, timeout=3600):
    """Cache the return value of the decorated function with the given key.

    Key can be a String or a function.
    If key is a function, it must have the same arguments as the decorated function,
    otherwise it cannot be called successfully.
    """

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            cache = get_cache()
            # Check if key is a function
            if callable(key):
                cache_key = key(*args, **kwargs)
            else:
                cache_key = key
            # Try to get the value from cache
            cached_val = cache.get(cache_key)
            if cached_val is None:
                # Call the original function and cache the result
                cached_val = f(*args, **kwargs)
                cache.set(cache_key, cached_val, timeout)
            return cached_val

        return wrapped

    return decorator

# === BLOCK 6 (label=human, source_idx=line975_human, name=checkCorpNums) ===
def checkCorpNums(self, MemberCorpNum, CorpNumList):
        """ 휴폐업조회 대량 확인, 최대 1000건
            args
                MemberCorpNum : 팝빌회원 사업자번호
                CorpNumList : 조회할 사업자번호 배열
            return
                휴폐업정보 Object as List
            raise
                PopbillException
        """
        if CorpNumList == None or len(CorpNumList) < 1:
            raise PopbillException(-99999999,"조죄할 사업자번호 목록이 입력되지 않았습니다.")

        postData = self._stringtify(CorpNumList)

        return self._httppost('/CloseDown',postData,MemberCorpNum)
