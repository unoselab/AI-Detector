# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line679_human, name=recent_update_frequencies) ===
def recent_update_frequencies(self):
        """ Returns the 10 most recent update frequencies.

        The given frequencies are computed as short-term frequencies!
        The 0th element of the list corresponds to the most recent frequency.
        """
        return list(reversed([(1.0 / p) for p in numpy.diff(self._recent_updates)]))

# === BLOCK 2 (label=human, source_idx=line4688_human, name=body_block_supplementary_material_render) ===
def body_block_supplementary_material_render(supp_tags, base_url=None):
    """fig and media tag caption may have supplementary material"""
    source_data = []
    for supp_tag in supp_tags:
        for block_content in body_block_content_render(supp_tag, base_url=base_url):
            if block_content != {}:
                if "content" in block_content:
                    del block_content["content"]
                source_data.append(block_content)
    return source_data

# === BLOCK 3 (label=lm, source_idx=line4093_lm, name=get_hdrgos_g_usrgos) ===
def get_hdrgos_g_usrgos(self, usrgos):
        """Return hdrgos which contain the usrgos."""
        hdrgos = []
        for hdrgo in self.hdrgos:
            if usrgos.issubset(hdrgo.usrgos):
                hdrgos.append(hdrgo)
        return hdrgos

# === BLOCK 4 (label=lm, source_idx=line4158_lm, name=correct) ===
def correct(word, known_words):
    """
    :param word: Word to correct
    :type word: string
    :param known_words: List of known words
    :type known_words: iterable of strings

    Given **word**, suggests a correction from **known_words**. If no reasonably close correction is found, returns
    **word**.
    """
    # TODO: Implement this function
    pass

# === BLOCK 5 (label=human, source_idx=line5469_human, name=get) ===
def get(self, key):
        """Vyper is essentially repository for configurations.
        `get` can retrieve any value given the key to use.
        `get` has the behavior of returning the value associated with the first
        place from where it is set. Viper will check in the following order:
        override, arg, env, config file, key/value store, default.
        """
        path = key.split(self._key_delimiter)

        lowercase_key = key.lower()
        val = self._find(lowercase_key)

        if val is None:
            source = self._find(path[0].lower())
            if source is not None and isinstance(source, dict):
                val = self._search_dict(source, path[1::])

        if val is None:
            return None

        return val

# === BLOCK 6 (label=lm, source_idx=line1357_lm, name=generate_checker) ===
def generate_checker(value):
    """Generate state checker for given value."""
    if isinstance(value, str):
        return f"{value} == state"
    elif isinstance(value, list):
        return f"state in {value}"
    else:
        raise ValueError(f"Invalid value: {value}")
