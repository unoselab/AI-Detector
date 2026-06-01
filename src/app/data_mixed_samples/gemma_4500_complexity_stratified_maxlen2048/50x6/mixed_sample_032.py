# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line5713_lm, name=url_unquote) ===
def url_unquote(s, charset='utf-8', errors='replace'):
    """URL decode a single string with a given decoding.

    Per default encoding errors are ignored.  If you want a different behavior
    you can set `errors` to ``'replace'`` or ``'strict'``.  In strict mode a
    `HTTPUnicodeError` is raised.

    :param s: the string to unquote.
    :param charset: the charset to be used.
    :param errors: the error handling for the charset decoding.
    """
    import urllib.parse

    try:
        return urllib.parse.unquote(s, encoding=charset, errors=errors)
    except UnicodeDecodeError as e:
        if errors == 'strict':
            class HTTPUnicodeError(UnicodeDecodeError):
                pass
            raise HTTPUnicodeError(e.encoding, e.object, e.start, e.end, e.reason) from e
        raise

# === BLOCK 2 (label=human, source_idx=line865_human, name=create_search_url) ===
def create_search_url(self):
        """ Generates (urlencoded) query string from stored key-values tuples

        :returns: A string containing all arguments in a url-encoded format
        """

        if len(self.searchterms) == 0:
            raise TwitterSearchException(1015)

        url = '?q='
        url += '+'.join([quote_plus(i) for i in self.searchterms])

        if self.attitude_filter is not None:
            url += '+%s' % quote_plus(self._attitudes[0 if self.attitude_filter else 1])

        if self.source_filter:
            url += '+%s' % quote_plus(self._source + self.source_filter)

        if self.link_filter:
            url += '+%s' % quote_plus(self._link)

        if self.question_filter:
            url += '+%s' % quote_plus(self._question)

        for key, value in self.arguments.items():
            url += '&%s=%s' % (quote_plus(key), (quote_plus(value)
                                                 if key != 'geocode'
                                                 else value))

        self.url = url
        return self.url

# === BLOCK 3 (label=human, source_idx=line4719_human, name=delete_action) ===
def delete_action(self, action, player_idx=0):
        """
        Return a new `Player` instance with the action(s) specified by
        `action` deleted from the action set of the player specified by
        `player_idx`. Deletion is not performed in place.

        Parameters
        ----------
        action : scalar(int) or array_like(int)
            Integer or array like of integers representing the action(s)
            to be deleted.

        player_idx : scalar(int), optional(default=0)
            Index of the player to delete action(s) for.

        Returns
        -------
        Player
            Copy of `self` with the action(s) deleted as specified.

        Examples
        --------
        >>> player = Player([[3, 0], [0, 3], [1, 1]])
        >>> player
        Player([[3, 0],
                [0, 3],
                [1, 1]])
        >>> player.delete_action(2)
        Player([[3, 0],
                [0, 3]])
        >>> player.delete_action(0, player_idx=1)
        Player([[0],
                [3],
                [1]])

        """
        payoff_array_new = np.delete(self.payoff_array, action, player_idx)
        return Player(payoff_array_new)

# === BLOCK 4 (label=lm, source_idx=line4218_lm, name=cast_to_str) ===
def cast_to_str(obj):
    """Return a string representation of a Seq or SeqRecord.

    Args:
        obj (str, Seq, SeqRecord): Biopython Seq or SeqRecord

    Returns:
        str: String representation of the sequence

    """
    if hasattr(obj, 'seq'):
        return str(obj.seq)
    return str(obj)

# === BLOCK 5 (label=human, source_idx=line3836_human, name=_iterbfs) ===
def _iterbfs(self, start, end=None, forward=True):
        """
        The forward parameter specifies whether it is a forward or backward
        traversal.  Returns a list of tuples where the first value is the hop
        value the second value is the node id.
        """
        queue, visited = deque([(start, 0)]), set([start])

        # the direction of the bfs depends on the edges that are sampled
        if forward:
            get_edges = self.out_edges
            get_next = self.tail
        else:
            get_edges = self.inc_edges
            get_next = self.head

        while queue:
            curr_node, curr_step = queue.popleft()
            yield (curr_node, curr_step)
            if curr_node == end:
                break
            for edge in get_edges(curr_node):
                tail = get_next(edge)
                if tail not in visited:
                    visited.add(tail)
                    queue.append((tail, curr_step + 1))

# === BLOCK 6 (label=lm, source_idx=line2816_lm, name=copy) ===
def copy(self, dest, src):
        """Copy element from sequence, member from mapping.

        :param dest: the destination
        :type dest: Pointer
        :param src: the source
        :type src: Pointer
        :return: resolved document
        :rtype: Target
        """
        if isinstance(dest, list):
            dest.append(src)
        elif isinstance(dest, dict):
            dest.update(src)
        else:
            setattr(dest, 'value', src)
        return dest
