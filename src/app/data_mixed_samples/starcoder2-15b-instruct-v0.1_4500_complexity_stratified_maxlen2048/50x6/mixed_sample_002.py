# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2149_lm, name=isidentifier) ===
def isidentifier(s, dotted=False):
    """
    A function equivalent to the str.isidentifier method on Py3
    """
    if not s:
        return False
    if not s[0].isalpha() and s[0]!= '_':
        return False
    if dotted:
        return all(isidentifier(part, dotted=False) for part in s.split('.'))
    return all(c.isalnum() or c == '_' for c in s[1:]) and s not in keyword.kwlist

# === BLOCK 2 (label=lm, source_idx=line1224_lm, name=extract_from_text) ===
def extract_from_text(text):
    """
    Extract ISBNs from a text.

    :param text: Some text.
    :returns: A list of canonical ISBNs found in the text.

    >>> extract_from_text("978-3-16-148410-0 9783161484100 9783161484100aa abcd 0136091814 0136091812 9780136091817 123456789X")
    ['9783161484100', '9783161484100', '9783161484100', '0136091814', '123456789X']
    """
    isbn_regex = r"(?:97[89])?\d{9}[\dx]"
    isbns = re.findall(isbn_regex, text)
    canonical_isbns = []
    for isbn in isbns:
        if isbn.endswith("x"):
            isbn = isbn[:-1] + "X"
        canonical_isbns.append(isbn)

    return canonical_isbns

# === BLOCK 3 (label=lm, source_idx=line1232_lm, name=redo_expansion_state) ===
def redo_expansion_state(self, ignore_not_existing_rows=False):
        """ Considers the tree to be collapsed and expand into all tree item with the flag set True """
        for row in range(self.model().rowCount()):
            index = self.model().index(row, 0)
            if self.isExpanded(index):
                self.collapse(index)
            self.expand(index)

# === BLOCK 4 (label=lm, source_idx=line4083_lm, name=trim_trailing_silence) ===
def trim_trailing_silence(self):
        """Trim the trailing silences of the pianorolls of all tracks. Trailing
        silences are considered globally."""
        for track in self.tracks:
            last_non_silent_row = 0
            for i, row in enumerate(track.pianoroll):
                if any(row):
                    last_non_silent_row = i
            track.pianoroll = track.pianoroll[:last_non_silent_row + 1]

# === BLOCK 5 (label=lm, source_idx=line1606_lm, name=mcmc_CH) ===
def mcmc_CH(self, walkerRatio, n_run, n_burn, mean_start, sigma_start, threadCount=1, init_pos=None, mpi=False):
        """
        runs mcmc on the parameter space given parameter bounds with CosmoHammerSampler
        returns the chain
        """
        if init_pos is None:
            init_pos = self.get_init_pos(mean_start, sigma_start)
        sampler = self.get_sampler(init_pos, walkerRatio, threadCount, mpi)
        sampler.run_mcmc(init_pos, n_burn + n_run, progress=True)
        return sampler.chain

# === BLOCK 6 (label=lm, source_idx=line325_lm, name=pypi_release) ===
def pypi_release(self):
        """Get the latest pypi release
        """
        url = f"https://pypi.org/pypi/{self.name}/json"
        response = requests.get(url)
        data = response.json()
        releases = data["releases"]
        latest_release = max(releases.keys())
        return latest_release
