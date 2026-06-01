# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line177_lm, name=Filter) ===
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
    if function is None:
      function = lambda row: not any(not entry for entry in row)
    return TextTable(
        [row for row in self.rows if function(row)],
        self.column_names,
        self.column_widths)

# === BLOCK 2 (label=human, source_idx=line1844_human, name=_summary) ===
def _summary(self, name=None):
        """
        Return a summarized representation.

        Parameters
        ----------
        name : str
            name to use in the summary representation

        Returns
        -------
        String with a summarized representation of the index
        """
        if len(self) > 0:
            head = self[0]
            if hasattr(head, 'format') and not isinstance(head, str):
                head = head.format()
            tail = self[-1]
            if hasattr(tail, 'format') and not isinstance(tail, str):
                tail = tail.format()
            index_summary = ', %s to %s' % (pprint_thing(head),
                                            pprint_thing(tail))
        else:
            index_summary = ''

        if name is None:
            name = type(self).__name__
        return '%s: %s entries%s' % (name, len(self), index_summary)

# === BLOCK 3 (label=lm, source_idx=line7795_lm, name=get) ===
def get(self, name=None):
        """Get initial yield value, or result of send(name) if name given."""
        if name is None:
            return self.initial
        else:
            return self.send(name)

# === BLOCK 4 (label=lm, source_idx=line3317_lm, name=watch_log_for_alive) ===
def watch_log_for_alive(self, nodes, from_mark=None, timeout=720, filename='system.log'):
        """
        Watch the log of this node until it detects that the provided other
        nodes are marked UP. This method works similarly to watch_log_for_death.

        We want to provide a higher default timeout when this is called on DSE.
        """
        return self.watch_log_for(nodes, from_mark, timeout, filename, 'alive')

# === BLOCK 5 (label=human, source_idx=line678_human, name=get_name_by_preorder) ===
def get_name_by_preorder( self, preorder_hash ):
        """
        Given a name preorder hash, get the associated name record.
        (It may be expired or revoked)
        """
        cur = self.db.cursor()
        return namedb_get_name_by_preorder_hash( cur, preorder_hash )

# === BLOCK 6 (label=human, source_idx=line1609_human, name=url) ===
def url(self):
        """The site-relative URL to the post."""
        url = u'{home_url}{permalink}'.format(home_url=settings.HOME_URL,
                                              permalink=self._permalink)
        url = re.sub(r'/{2,}', r'/', url)
        return url
