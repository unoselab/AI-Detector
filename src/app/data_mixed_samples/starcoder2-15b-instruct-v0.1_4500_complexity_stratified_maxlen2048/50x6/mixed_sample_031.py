# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line592_lm, name=fulltext_add) ===
def fulltext_add(self, index, docs):
        """
        Adds documents to the search index.
        """
        for doc in docs:
            self.fulltext_index[index].add(doc)

# === BLOCK 2 (label=human, source_idx=line488_human, name=data) ===
def data(self, index, role=Qt.DisplayRole):
        """Override Qt method"""
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return to_qvariant()
        row = index.row()
        column = index.column()

        name, state = self.row(row)

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if column == 0:
                return to_qvariant(name)
        elif role == Qt.CheckStateRole:
            if column == 0:
                if state:
                    return Qt.Checked
                else:
                    return Qt.Unchecked
            if column == 1:
                return to_qvariant(state)
        return to_qvariant()

# === BLOCK 3 (label=human, source_idx=line4974_human, name=dependents_of_addresses) ===
def dependents_of_addresses(self, addresses):
    """Given an iterable of addresses, yield all of those addresses dependents."""
    seen = OrderedSet(addresses)
    for address in addresses:
      seen.update(self._dependent_address_map[address])
      seen.update(self._implicit_dependent_address_map[address])
    return seen

# === BLOCK 4 (label=human, source_idx=line1322_human, name=_init_client) ===
def _init_client():
    """Initialize connection and create table if needed
    """
    if client is not None:
        return

    global _mysql_kwargs, _table_name
    _mysql_kwargs = {
        'host': __opts__.get('mysql.host', '127.0.0.1'),
        'user': __opts__.get('mysql.user', None),
        'passwd': __opts__.get('mysql.password', None),
        'db': __opts__.get('mysql.database', _DEFAULT_DATABASE_NAME),
        'port': __opts__.get('mysql.port', 3306),
        'unix_socket': __opts__.get('mysql.unix_socket', None),
        'connect_timeout': __opts__.get('mysql.connect_timeout', None),
        'autocommit': True,
    }
    _table_name = __opts__.get('mysql.table_name', _table_name)
    # TODO: handle SSL connection parameters

    for k, v in _mysql_kwargs.items():
        if v is None:
            _mysql_kwargs.pop(k)
    kwargs_copy = _mysql_kwargs.copy()
    kwargs_copy['passwd'] = "<hidden>"
    log.info("mysql_cache: Setting up client with params: %r", kwargs_copy)
    # The MySQL client is created later on by run_query
    _create_table()

# === BLOCK 5 (label=lm, source_idx=line1638_lm, name=get_learned_skills) ===
def get_learned_skills(self, lang):
        """
        Return the learned skill objects sorted by the order they were learned
        in.
        """
        return sorted(self.skills, key=lambda skill: skill.order_learned)

# === BLOCK 6 (label=lm, source_idx=line3822_lm, name=time2dir) ===
def time2dir(tstamp):
    """Given a :class:`datetime.datetime` object,
    return a path assembled with :func:`os.path.join`
    for the levels."""
    year = str(tstamp.year)
    month = str(tstamp.month).zfill(2)
    day = str(tstamp.day).zfill(2)
    hour = str(tstamp.hour).zfill(2)
    return os.path.join(year, month, day, hour)
