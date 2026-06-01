# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1944_human, name=get_cases) ===
def get_cases(self, skip_ws=False):
        """Returns a list of 2-tuples (condition, value).

        If an ELSE exists condition is None.
        """
        CONDITION = 1
        VALUE = 2

        ret = []
        mode = CONDITION

        for token in self.tokens:
            # Set mode from the current statement
            if token.match(T.Keyword, 'CASE'):
                continue

            elif skip_ws and token.ttype in T.Whitespace:
                continue

            elif token.match(T.Keyword, 'WHEN'):
                ret.append(([], []))
                mode = CONDITION

            elif token.match(T.Keyword, 'THEN'):
                mode = VALUE

            elif token.match(T.Keyword, 'ELSE'):
                ret.append((None, []))
                mode = VALUE

            elif token.match(T.Keyword, 'END'):
                mode = None

            # First condition without preceding WHEN
            if mode and not ret:
                ret.append(([], []))

            # Append token depending of the current mode
            if mode == CONDITION:
                ret[-1][0].append(token)

            elif mode == VALUE:
                ret[-1][1].append(token)

        # Return cases list
        return ret

# === BLOCK 2 (label=lm, source_idx=line5359_lm, name=create_session) ===
def create_session(target='', timeout_sec=10):
  """Create an intractive TensorFlow session.

  Helper function that creates TF session that uses growing GPU memory
  allocation and opration timeout. 'allow_growth' flag prevents TF
  from allocating the whole GPU memory an once, which is useful
  when having multiple python sessions sharing the same GPU.
  """

# === BLOCK 3 (label=human, source_idx=line5360_human, name=load_subcommands) ===
def load_subcommands(group):
    """
    Decorator used to load subcommands from a given ``pkg_resources``
    entrypoint group.  Each function must be appropriately decorated
    with the ``cli_tools`` decorators to be considered an extension.

    :param group: The name of the ``pkg_resources`` entrypoint group.
    """

    def decorator(func):
        adaptor = ScriptAdaptor._get_adaptor(func)
        adaptor._add_extensions(group)
        return func
    return decorator

# === BLOCK 4 (label=lm, source_idx=line7728_lm, name=load) ===
def load(self, session_id=None):
        """ Load the session from the store.
        session_id can be:
        - None: load from cookie
        - '': create a new cookieless session_id
        - a string which is the session_id to be used.
        """
        if session_id is None:
            session_id = self.get_session_id()
        if session_id is None:
            return
        if session_id == '':
            self.session_id = session_id
            self.session = {}
            return
        try:
            self.session = self.store.load(session_id)
        except KeyError:
            self.session = {}
        self.session_id = session_id

# === BLOCK 5 (label=lm, source_idx=line2810_lm, name=load) ===
def load(file_path, parse_line_fn):
  """Loads a text embedding into memory as a numpy matrix.

  Args:
    file_path: Path to the text embedding file.
    parse_line_fn: callback function to parse each file line.

  Returns:
    A tuple of (list of vocabulary tokens, numpy matrix of embedding vectors).

  Raises:
    ValueError: if the data in the sstable is inconsistent.
  """

# === BLOCK 6 (label=human, source_idx=line495_human, name=when_closed) ===
def when_closed(self):
        """
        Returns a Deferred that callback()'s (with this Circuit instance)
        when this circuit hits CLOSED or FAILED.
        """
        if self.state in ['CLOSED', 'FAILED']:
            return defer.succeed(self)
        return self._when_closed.when_fired()
