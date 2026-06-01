# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3122_lm, name=get_for_update) ===
def get_for_update(self, connection_name='DEFAULT', **kwargs):

        """
        http://docs.sqlalchemy.org/en/latest/orm/query.html?highlight=update#sqlalchemy.orm.query.Query.with_for_update  # noqa
        """

        return self.with_for_update(**kwargs)

# === BLOCK 2 (label=lm, source_idx=line3738_lm, name=same) ===
def same(d1, d2):
    """! @brief Test whether two sequences contain the same values.

    Unlike a simple equality comparison, this function works as expected when the two sequences
    are of different types, such as a list and bytearray. The sequences must return
    compatible types from indexing.
    """
    if len(d1) != len(d2):
        return False
    for i in range(len(d1)):
        if d1[i] != d2[i]:
            return False
    return True

# === BLOCK 3 (label=human, source_idx=line4856_human, name=ParseOptions) ===
def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    storage_file = cls._ParseStringOption(options, 'storage_file')

    setattr(configuration_object, '_storage_file_path', storage_file)

# === BLOCK 4 (label=lm, source_idx=line2435_lm, name=query_scene_loaded) ===
def query_scene_loaded(cli, scene_name):
    """
    Requests status on whether a scene is loaded or not.
    :param cli:
    :param scene_name:
    :return: bool
    """
    return cli.query(f'scene_loaded {scene_name}')

# === BLOCK 5 (label=human, source_idx=line753_human, name=parse_ini_file) ===
def parse_ini_file(self, path):
        """Parse ini file at ``path`` and return dict."""
        cfgobj = ConfigObj(path, list_values=False)

        def extract_section(namespace, d):
            cfg = {}
            for key, val in d.items():
                if isinstance(d[key], dict):
                    cfg.update(extract_section(namespace + [key], d[key]))
                else:
                    cfg['_'.join(namespace + [key]).upper()] = val

            return cfg

        return extract_section([], cfgobj.dict())

# === BLOCK 6 (label=human, source_idx=line4189_human, name=prep_jid) ===
def prep_jid(nocache=False, passed_jid=None):
    """
    Return a job id and prepare the job id directory
    This is the function responsible for making sure jids don't collide (unless
    its passed a jid)
    So do what you have to do to make sure that stays the case
    """
    if passed_jid is None:
        jid = salt.utils.jid.gen_jid(__opts__)
    else:
        jid = passed_jid

    cb_ = _get_connection()

    try:
        cb_.add(six.text_type(jid),
               {'nocache': nocache},
               ttl=_get_ttl(),
               )
    except couchbase.exceptions.KeyExistsError:
        # TODO: some sort of sleep or something? Spinning is generally bad practice
        if passed_jid is None:
            return prep_jid(nocache=nocache)

    return jid
