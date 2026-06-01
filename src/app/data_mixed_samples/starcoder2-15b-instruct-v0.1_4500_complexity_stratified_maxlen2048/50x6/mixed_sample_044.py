# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line297_human, name=db_exec_with_cursor) ===
def db_exec_with_cursor(self, cursor, sql: str, *args) -> int:
        """Executes SQL on a supplied cursor, with "?" placeholders,
        substituting in the arguments. Returns number of rows affected."""
        sql = self.localize_sql(sql)
        try:
            debug_sql(sql, args)
            cursor.execute(sql, args)
            return cursor.rowcount
        except:  # nopep8
            log.exception("db_exec_with_cursor: SQL was: " + sql)
            raise

# === BLOCK 2 (label=human, source_idx=line690_human, name=_remove_compression_suffix_if_present) ===
def _remove_compression_suffix_if_present(self, filename):
        """
        If the given filename ends in one of the compression suffixes that
        datacache knows how to deal with, remove the suffix (since we expect
        the result of downloading to be a decompressed file)
        """
        for ext in [".gz", ".gzip", ".zip"]:
            if filename.endswith(ext):
                return filename[:-len(ext)]
        return filename

# === BLOCK 3 (label=lm, source_idx=line84_lm, name=_multiplexed_buffer_helper) ===
def _multiplexed_buffer_helper(self, response):
        """A generator of multiplexed data blocks read from a buffered
        response."""
        while True:
            header = response.read(8)
            if len(header) < 8:
                break
            length = int.from_bytes(header[:4], byteorder='big')
            type = int.from_bytes(header[4:], byteorder='big')
            data = response.read(length)
            yield data

# === BLOCK 4 (label=lm, source_idx=line1946_lm, name=as_span) ===
def as_span(cls, lower_version=None, upper_version=None,
                lower_inclusive=True, upper_inclusive=True):
        """Create a range from lower_version..upper_version.

        Args:
            lower_version: Version object representing lower bound of the range.
            upper_version: Version object representing upper bound of the range.

        Returns:
            `VersionRange` object.
        """
        return cls(lower_version, upper_version, lower_inclusive, upper_inclusive)

# === BLOCK 5 (label=lm, source_idx=line4283_lm, name=connectCached) ===
def connectCached(self, endpoint, protocolFactory,
                      extraWork=lambda x: x,
                      extraHash=None):
        """
        See module docstring

        @param endpoint:
        @param protocolFactory:
        @param extraWork:
        @param extraHash:

        @return: the D
        """
        key = (endpoint, protocolFactory, extraHash)
        if key in self.cache:
            return self.cache[key]
        d = self.connect(endpoint, protocolFactory, extraWork=extraWork)
        self.cache[key] = d
        return d

# === BLOCK 6 (label=human, source_idx=line1360_human, name=_gatk4_cmd) ===
def _gatk4_cmd(jvm_opts, params, data):
    """Retrieve unified command for GATK4, using 'gatk'. GATK3 is 'gatk3'.
    """
    gatk_cmd = utils.which(os.path.join(os.path.dirname(os.path.realpath(sys.executable)), "gatk"))
    return "%s && export PATH=%s:\"$PATH\" && gatk --java-options '%s' %s" % \
        (utils.clear_java_home(), utils.get_java_binpath(gatk_cmd),
         " ".join(jvm_opts), " ".join([str(x) for x in params]))
