# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line177_human, name=Filter) ===
def Filter(self, function=None):
    """Construct Textable from the rows of which the function returns true.


    Args:
      function: A function applied to each row which returns a bool. If
                function is None, all rows with empty column values are
                removed.
    Returns:
      A new TextTable()

    Raises:
      TableError: When an invalid row entry is Append()'d
    """
    flat = lambda x: x if isinstance(x, str) else ''.join([flat(y) for y in x])
    if function is None:
      function = lambda row: bool(flat(row.values))

    new_table = self.__class__()
    # pylint: disable=protected-access
    new_table._table = [self.header]
    for row in self:
      if function(row) is True:
        new_table.Append(row)
    return new_table

# === BLOCK 2 (label=human, source_idx=line5870_human, name=check_for_errors) ===
def check_for_errors(self):
        """Check connection and channel for errors.

        :raises AMQPChannelError: Raises if the channel encountered an error.
        :raises AMQPConnectionError: Raises if the connection
                                     encountered an error.
        :return:
        """
        try:
            self._connection.check_for_errors()
        except AMQPConnectionError:
            self.set_state(self.CLOSED)
            raise

        if self.exceptions:
            exception = self.exceptions[0]
            if self.is_open:
                self.exceptions.pop(0)
            raise exception

        if self.is_closed:
            raise AMQPChannelError('channel was closed')

# === BLOCK 3 (label=lm, source_idx=line7140_lm, name=RootNode) ===
def RootNode(self):
        """Return our current root node and appropriate adapter for it"""
        if self.root is None:
            return None, None
        return self.root, self.root.adapter

# === BLOCK 4 (label=human, source_idx=line3749_human, name=_insert_or_replace_entity) ===
def _insert_or_replace_entity(entity):
    """
    Constructs an insert or replace entity request.
    """
    _validate_entity(entity)

    request = HTTPRequest()
    request.method = 'PUT'
    request.headers = [_DEFAULT_CONTENT_TYPE_HEADER,
                        _DEFAULT_ACCEPT_HEADER]
    request.body = _get_request_body(_convert_entity_to_json(entity))

    return request

# === BLOCK 5 (label=lm, source_idx=line2075_lm, name=create_files) ===
def create_files(filedef, cleanup=True):
    """Contextmanager that creates a directory structure from a yaml
       descripttion.
    """
    import os
    import shutil
    import tempfile
    import yaml

# === BLOCK 6 (label=lm, source_idx=line1550_lm, name=_config_section) ===
def _config_section(config, section):
    """Read the configuration file and return a section."""
    section = config.items(section)
    return dict(section)
