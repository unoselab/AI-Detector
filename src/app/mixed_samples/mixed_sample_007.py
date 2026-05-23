# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1847_human, name=remove_columns) ===
def remove_columns(self, column_names, inplace=False):
        """
        Returns an SFrame with one or more columns removed.

        If inplace == False (default) this operation does not modify the
        current SFrame, returning a new SFrame.

        If inplace == True, this operation modifies the current
        SFrame, returning self.

        Parameters
        ----------
        column_names : list or iterable
            A list or iterable of column names.

        inplace : bool, optional. Defaults to False.
            Whether the SFrame is modified in place.

        Returns
        -------
        out : SFrame
            The SFrame with given columns removed.

        Examples
        --------
        >>> sf = turicreate.SFrame({'id': [1, 2, 3], 'val1': ['A', 'B', 'C'], 'val2' : [10, 11, 12]})
        >>> res = sf.remove_columns(['val1', 'val2'])
        >>> res
        +----+
        | id |
        +----+
        | 1  |
        | 2  |
        | 3  |
        +----+
        [3 rows x 1 columns]
        """
        column_names = list(column_names)
        existing_columns = dict((k, i) for i, k in enumerate(self.column_names()))

        for name in column_names:
            if name not in existing_columns:
                raise KeyError('Cannot find column %s' % name)

        # Delete it going backwards so we don't invalidate indices
        deletion_indices = sorted(existing_columns[name] for name in column_names)

        if inplace:
            ret = self
        else:
            ret = self.copy()

        for colid in reversed(deletion_indices):
            with cython_context():
                ret.__proxy__.remove_column(colid)

        ret._cache = None
        return ret

# === BLOCK 2 (label=human, source_idx=line2028_human, name=handle_absolute) ===
def handle_absolute(self, event):
        """Absolute mouse position on the screen."""
        point = self._get_absolute(event)
        x_pos = round(point.x)
        y_pos = round(point.y)
        x_event, y_event = self.emulate_abs(x_pos, y_pos, self.timeval)
        self.events.append(x_event)
        self.events.append(y_event)

# === BLOCK 3 (label=lm, source_idx=line2320_lm, name=split_long_sentence) ===
def split_long_sentence(sentence, words_per_line):
    """Takes a sentence and adds a newline every "words_per_line" words.

    Parameters
    ----------
    sentence: str
        Sentene to split
    words_per_line: double
        Add a newline every this many words
    """
    words = sentence.split()
    result = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(current_line) == words_per_line:
            result.append(' '.join(current_line))
            current_line = []
    if current_line:
        result.append(' '.join(current_line))
    return '\n'.join(result)

# === BLOCK 4 (label=human, source_idx=line2374_human, name=create_token) ===
def create_token(self, user):
        """
        Create a signed token from a user.

        """
        # The password is expected to be a secure hash but we hash it again
        # for additional safety. We default to MD5 to minimize the length of
        # the token. (Remember, if an attacker obtains the URL, he can already
        # log in. This isn't high security.)
        h = crypto.pbkdf2(
            self.get_revocation_key(user),
            self.salt,
            self.iterations,
            digest=self.digest,
        )
        return self.sign(self.packer.pack_pk(user.pk) + h)

# === BLOCK 5 (label=human, source_idx=line2592_human, name=match) ===
def match(self, path_pattern):
        """
        Return True if this path matches the given pattern.
        """
        cf = self._flavour.casefold
        path_pattern = cf(path_pattern)
        drv, root, pat_parts = self._flavour.parse_parts((path_pattern,))
        if not pat_parts:
            raise ValueError("empty pattern")
        if drv and drv != cf(self._drv):
            return False
        if root and root != cf(self._root):
            return False
        parts = self._cparts
        if drv or root:
            if len(pat_parts) != len(parts):
                return False
            pat_parts = pat_parts[1:]
        elif len(pat_parts) > len(parts):
            return False
        for part, pat in zip(reversed(parts), reversed(pat_parts)):
            if not fnmatch.fnmatchcase(part, pat):
                return False
        return True

# === BLOCK 6 (label=human, source_idx=line842_human, name=write) ===
def write(self, data):
        """Writes json data to the output directory."""
        cnpj, data = data

        path = os.path.join(self.output, '%s.json' % cnpj)
        with open(path, 'w') as f:
            json.dump(data, f, encoding='utf-8')
