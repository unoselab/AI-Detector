# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1935_lm, name=get_ast) ===
def get_ast(self):
        """
        Processes each class with AST enabled and returns a dictionary with all single ASTs
        Classnames as keys.

        :return: an dictionary for all classes
        :rtype: dict
        """
        ast_dict = {}
        for class_name, class_obj in self.classes.items():
            if class_obj.ast_enabled:
                ast_dict[class_name] = class_obj.ast
        return ast_dict

# === BLOCK 2 (label=human, source_idx=line1720_human, name=call) ===
def call(corofunc, *args, **kwargs):
    """
    :return:
        a delegator function that returns a coroutine object by calling
        ``corofunc(seed_tuple, *args, **kwargs)``.
    """
    corofunc = _ensure_coroutine_function(corofunc)
    def f(seed_tuple):
        return corofunc(seed_tuple, *args, **kwargs)
    return f

# === BLOCK 3 (label=lm, source_idx=line3680_lm, name=emulate) ===
def emulate(self, context=None, start=None, end=None, arch_mode=None, hooks=None, max_instrs=None, print_asm=False):
        """Emulate native code.

        Args:
            context (dict): Processor context (register and/or memory).
            start (int): Start address.
            end (int): End address.
            arch_mode (int): Architecture mode.
            hooks (dict): Hooks by address.
            max_instrs (int): Maximum number of instructions to execute.
            print_asm (bool): Print asm.

        Returns:
            dict: Processor context.
        """
        if context is None:
            context = {}
        if start is None:
            start = 0
        if end is None:
            end = start + 1
        if arch_mode is None:
            arch_mode = 0
        if hooks is None:
            hooks = {}
        if max_instrs is None:
            max_instrs = 100
        if print_asm is False:
            print_asm = False

        while start < end and max_instrs > 0:
            if print_asm:
                print(f"0x{start:x}: {asm}")
            if start in hooks:
                hooks[start](self, context)
            start += 1
            max_instrs -= 1

        return context

# === BLOCK 4 (label=human, source_idx=line2673_human, name=error_and_result) ===
def error_and_result(f):
    """
    Format task result into json dictionary `{'data': task return value}` if no
    exception was raised during the task execution. If there was raised an
    exception during task execution, formats task result into dictionary
    `{'error': exception message with traceback}`.
    """

    @wraps(f)
    def error_and_result_decorator(*args, **kwargs):
        return error_and_result_decorator_inner_fn(f, False, *args, **kwargs)

    return error_and_result_decorator

# === BLOCK 5 (label=human, source_idx=line3515_human, name=_write_standard) ===
def _write_standard(self, message, extra):
        """
        Writes a standard log statement

        @param message: The message to write
        @param extra: The object to pull defaults from
        """
        level = extra['level']
        if self.include_extra:
            del extra['timestamp']
            del extra['level']
            del extra['logger']
            if len(extra) > 0:
                message += " " + str(extra)

        if level == 'INFO':
            self.logger.info(message)
        elif level == 'DEBUG':
            self.logger.debug(message)
        elif level == 'WARNING':
            self.logger.warning(message)
        elif level == 'ERROR':
            self.logger.error(message)
        elif level == 'CRITICAL':
            self.logger.critical(message)
        else:
            self.logger.debug(message)

# === BLOCK 6 (label=lm, source_idx=line1003_lm, name=_get_user_info) ===
def _get_user_info(self, access_token, id_token):
        """
        Extracts the user info payload from the Id Token.

        Example return value:

        {
            "at_hash": "<HASH>",
            "aud": "<HASH>",
            "email_verified": true,
            "email": "fsurname@mozilla.com",
            "exp": 1551259495,
            "family_name": "Surname",
            "given_name": "Firstname",
            "https://sso.mozilla.com/claim/groups": [
                "all_scm_level_1",
                "all_scm_level_2",
                "all_scm_level_3",
                # ...
            ],
            "iat": 1550654695,
            "iss": "https://auth.mozilla.auth0.com/",
            "name": "Firstname Surname",
            "nickname": "Firstname Surname",
            "nonce": "<HASH>",
            "picture": "<GRAVATAR_URL>",
            "sub": "ad|Mozilla-LDAP|fsurname",
            "updated_at": "2019-02-20T09:24:55.449Z",
        }
        """
        id_token_parts = id_token.split('.')
        user_info = json.loads(base64.b64decode(id_token_parts[1] + '=' * (-len(id_token_parts[1]) % 4)))
        return user_info
