# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1601_lm, name=clean) ===
def clean(self, initial_epoch):
        """ Remove entries from database that would get overwritten """
        # Remove entries from database that would get overwritten
        for entry in self.entries:
            if entry.epoch > initial_epoch:
                self.entries.remove(entry)

# === BLOCK 2 (label=human, source_idx=line1757_human, name=list_length) ===
def list_length(queue, backend='sqlite'):
    """
    Provide the number of items in a queue

    CLI Example:

    .. code-block:: bash

        salt-run queue.list_length myqueue
        salt-run queue.list_length myqueue backend=sqlite
    """
    queue_funcs = salt.loader.queues(__opts__)
    cmd = '{0}.list_length'.format(backend)
    if cmd not in queue_funcs:
        raise SaltInvocationError('Function "{0}" is not available'.format(cmd))
    ret = queue_funcs[cmd](queue=queue)
    return ret

# === BLOCK 3 (label=lm, source_idx=line6375_lm, name=update_record) ===
def update_record(self, **attrs):
        # The `_record` is to avoid conflicts with MutableMapping.update.
        """
        Update the record, modifying any number of its attributes (except
        ``id``).  ``update_record`` takes the same keyword arguments as
        :meth:`Domain.create_record`; pass in only those attributes that you
        want to update.

        :return: an updated `DomainRecord` object
        :rtype: DomainRecord
        :raises DOAPIError: if the API endpoint replies with an error
        """
        return self._record.update(**attrs)

# === BLOCK 4 (label=lm, source_idx=line2853_lm, name=byteslice_select) ===
def byteslice_select(offset, bv_di, bv_do):
    """ Selects a slice of length 8*n aligned on a byte from a bit-vector
            offset - (i) byte offset of the slice
            bv_di  - (i) bit vector where the slice is taken from; must len(bv_di) = 8*m
            bv_do  - (o) selected slice; must len(bv_do) = 8*n, n<=m; len(bv_do) defines the number of bit in the slice
    """
    assert len(bv_di) % 8 == 0
    assert len(bv_do) % 8 == 0
    assert offset < len(bv_di)
    assert offset + len(bv_do) <= len(bv_di)
    bv_do.clear()
    for i in range(len(bv_do)):
        bv_do[i] = bv_di[offset + i]

# === BLOCK 5 (label=human, source_idx=line5540_human, name=_is_missing_tags_strict) ===
def _is_missing_tags_strict(self):
        """
        Return whether missing_tags is set to strict.

        """
        val = self.missing_tags

        if val == MissingTags.strict:
            return True
        elif val == MissingTags.ignore:
            return False

        raise Exception("Unsupported 'missing_tags' value: %s" % repr(val))

# === BLOCK 6 (label=human, source_idx=line1417_human, name=read_config) ===
def read_config(
        config_filepath,
        logger=logging.getLogger('ProsperCommon'),
):
    """fetch and parse config file

    Args:
        config_filepath (str): path to config file.  abspath > relpath
        logger (:obj:`logging.Logger`): logger to catch error msgs

    """
    config_parser = configparser.ConfigParser(
        interpolation=ExtendedInterpolation(),
        allow_no_value=True,
        delimiters=('='),
        inline_comment_prefixes=('#')
    )
    logger.debug('config_filepath=%s', config_filepath)

    with open(config_filepath, 'r') as filehandle:
        config_parser.read_file(filehandle)

    return config_parser
