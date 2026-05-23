# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2768_human, name=get_day_name) ===
def get_day_name(self) -> str:
        """ Returns the day name """
        weekday = self.value.isoweekday() - 1
        return calendar.day_name[weekday]

# === BLOCK 2 (label=lm, source_idx=line460_lm, name=is_applicable) ===
def is_applicable(cls, conf):
        """Return whether this promoter is applicable for given conf"""
        return cls.name in conf.promoters

# === BLOCK 3 (label=lm, source_idx=line1138_lm, name=shift_display) ===
def shift_display(self, amount):
        """Shift the display. Use negative amounts to shift left and positive
        amounts to shift right."""
        if amount < 0:
            self.display = self.display[-amount:] + self.display[: -amount]
        else:
            self.display = self.display[amount:] + self.display[:amount]

# === BLOCK 4 (label=lm, source_idx=line466_lm, name=_head) ===
def _head(self, uri):
        """
        Handles the communication with the API when performing a HEAD request
        on a specific resource managed by this class. Returns the headers
        contained in the response.
        """
        response = requests.head(uri)
        return response.headers

# === BLOCK 5 (label=human, source_idx=line2068_human, name=_translate_pattern) ===
def _translate_pattern(self, pattern, anchor=True, prefix=None,
                           is_regex=False):
        """Translate a shell-like wildcard pattern to a compiled regular
        expression.

        Return the compiled regex.  If 'is_regex' true,
        then 'pattern' is directly compiled to a regex (if it's a string)
        or just returned as-is (assumes it's a regex object).
        """
        if is_regex:
            if isinstance(pattern, str):
                return re.compile(pattern)
            else:
                return pattern

        if _PYTHON_VERSION > (3, 2):
            # ditch start and end characters
            start, _, end = self._glob_to_re('_').partition('_')

        if pattern:
            pattern_re = self._glob_to_re(pattern)
            if _PYTHON_VERSION > (3, 2):
                assert pattern_re.startswith(start) and pattern_re.endswith(end)
        else:
            pattern_re = ''

        base = re.escape(os.path.join(self.base, ''))
        if prefix is not None:
            # ditch end of pattern character
            if _PYTHON_VERSION <= (3, 2):
                empty_pattern = self._glob_to_re('')
                prefix_re = self._glob_to_re(prefix)[:-len(empty_pattern)]
            else:
                prefix_re = self._glob_to_re(prefix)
                assert prefix_re.startswith(start) and prefix_re.endswith(end)
                prefix_re = prefix_re[len(start): len(prefix_re) - len(end)]
            sep = os.sep
            if os.sep == '\\':
                sep = r'\\'
            if _PYTHON_VERSION <= (3, 2):
                pattern_re = '^' + base + sep.join((prefix_re,
                                                    '.*' + pattern_re))
            else:
                pattern_re = pattern_re[len(start): len(pattern_re) - len(end)]
                pattern_re = r'%s%s%s%s.*%s%s' % (start, base, prefix_re, sep,
                                                  pattern_re, end)
        else:  # no prefix -- respect anchor flag
            if anchor:
                if _PYTHON_VERSION <= (3, 2):
                    pattern_re = '^' + base + pattern_re
                else:
                    pattern_re = r'%s%s%s' % (start, base, pattern_re[len(start):])

        return re.compile(pattern_re)

# === BLOCK 6 (label=human, source_idx=line2510_human, name=add_area) ===
def add_area(self, uri):
        """
        Record information about a new Upload Area

        :param UploadAreaURI uri: An Upload Area URI.
        """
        if uri.area_uuid not in self._config.upload.areas:
            self._config.upload.areas[uri.area_uuid] = {'uri': uri.uri}
        self.save()
