# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2367_lm, name=returnChartData) ===
def returnChartData(self, currencyPair, period, start=0, end=2**32-1):
        """Returns candlestick chart data. Required GET parameters are
        "currencyPair", "period" (candlestick period in seconds; valid values
        are 300, 900, 1800, 7200, 14400, and 86400), "start", and "end".
        "Start" and "end" are given in UNIX timestamp format and used to
        specify the date range for the data returned."""
        if not isinstance(currencyPair, str):
            raise TypeError("currencyPair must be a string")
        if not isinstance(period, int):
            raise TypeError("period must be an integer")
        if not isinstance(start, int):
            raise TypeError("start must be an integer")
        if not isinstance(end, int):
            raise TypeError("end must be an integer")
        if period not in (300, 900, 1800, 7200, 14400, 86400):
            raise ValueError("period must be one of 300, 900, 1800, 7200, 14400, or 86400")
        if start < 0:
            raise ValueError("start must be non-negative")
        if end < start:
            raise ValueError("end must be greater than or equal to start")
        return self.api_query(command='returnChartData',
                               currencyPair=currencyPair,
                               period=period,
                               start=start,
                               end=end)

# === BLOCK 2 (label=lm, source_idx=line2596_lm, name=box_coordinates) ===
def box_coordinates(self):
        """Returns a thumbnail's coordinates."""
        return self.box

# === BLOCK 3 (label=human, source_idx=line2852_human, name=_needs_git) ===
def _needs_git(func):
    """
    Small decorator to make sure we have the git repo, or report error
    otherwise.
    """

    @wraps(func)
    def myfunc(*args, **kwargs):
        if not WITH_GIT:
            raise RuntimeError(
                "Dulwich library not available, can't extract info from the "
                "git repos."
            )
        return func(*args, **kwargs)

    return myfunc

# === BLOCK 4 (label=human, source_idx=line1438_human, name=add_to_manifest) ===
def add_to_manifest(self, rel_path, checksums):
        # type: (Text, Dict[str,str]) -> None
        """Add files to the research object manifest."""
        self.self_check()
        if posixpath.isabs(rel_path):
            raise ValueError("rel_path must be relative: %s" % rel_path)

        if posixpath.commonprefix(["data/", rel_path]) == "data/":
            # payload file, go to manifest
            manifest = "manifest"
        else:
            # metadata file, go to tag manifest
            manifest = "tagmanifest"

        # Add checksums to corresponding manifest files
        for (method, hash_value) in checksums.items():
            # File not in manifest because we bailed out on
            # existence in bagged_size above
            manifestpath = os.path.join(
                self.folder, "%s-%s.txt" % (manifest, method.lower()))
            # encoding: match Tag-File-Character-Encoding: UTF-8
            # newline: ensure LF also on Windows
            with open(manifestpath, "a", encoding=ENCODING, newline='\n') \
                    as checksum_file:
                line = u"%s  %s\n" % (hash_value, rel_path)
                _logger.debug(u"[provenance] Added to %s: %s", manifestpath, line)
                checksum_file.write(line)

# === BLOCK 5 (label=human, source_idx=line1494_human, name=to_env_var) ===
def to_env_var(env_var: str, value) -> str:
    """
    Create an environment variable from a name and a value.

    This generates a shell-compatible representation of an
    environment variable that is assigned a YAML representation of
    a value.

    Args:
        env_var (str): Name of the environment variable.
        value (Any): A value we convert from.
    """
    val = to_yaml(value)
    ret_val = "%s=%s" % (env_var, escape_yaml(val))
    return ret_val

# === BLOCK 6 (label=lm, source_idx=line989_lm, name=text_filter) ===
def text_filter(regex_base, value):
    """
    Helper method to regex replace images with captions in different markups
    """
    regex = re.compile(regex_base)
    return regex.sub(r'![\2](\1)', value)
