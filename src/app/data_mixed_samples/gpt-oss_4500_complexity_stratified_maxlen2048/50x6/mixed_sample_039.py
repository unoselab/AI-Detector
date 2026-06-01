# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line430_lm, name=get_version_from_dirname) ===
def get_version_from_dirname(name, parent):
    """Extracted sdist"""
    import os
    import re
    from packaging.version import Version, InvalidVersion

# === BLOCK 2 (label=human, source_idx=line514_human, name=__access) ===
def __access(self, ts):
    """ Record an API access. """
    with self.connection:
      self.connection.execute("INSERT OR REPLACE INTO access_timestamp (timestamp, domain) VALUES (?, ?)",
                              (ts, self.domain))

# === BLOCK 3 (label=lm, source_idx=line1407_lm, name=ts_to_str) ===
def ts_to_str(jwt_dict):
    """Convert timestamps in JWT to human readable dates.

    Args:
      jwt_dict: dict
        JWT with some keys containing timestamps.

    Returns:
      dict: Copy of input dict where timestamps have been replaced with human readable
      dates.

    """
    import copy
    from datetime import datetime

    def _convert(val):
        if isinstance(val, dict):
            return {k: _convert(v) for k, v in val.items()}
        if isinstance(val, (list, tuple)):
            converted = [_convert(v) for v in val]
            return type(val)(converted)
        if isinstance(val, (int, float)):
            try:
                # Treat as Unix timestamp (seconds since epoch)
                dt = datetime.utcfromtimestamp(val)
                # ISO 8601 format with trailing 'Z' to indicate UTC
                return dt.isoformat() + "Z"
            except (OverflowError, OSError, ValueError):
                return val
        return val

    return _convert(copy.deepcopy(jwt_dict))

# === BLOCK 4 (label=lm, source_idx=line4686_lm, name=dump) ===
def dump(self):
        """Write coincidence counts into a Python pickle"""
        import os
        import pickle

        # Retrieve the data to be saved
        if not hasattr(self, "coincidence_counts"):
            raise AttributeError("Missing 'coincidence_counts' attribute")
        data = self.coincidence_counts

        # Determine the output file name
        if not hasattr(self, "filename"):
            raise AttributeError("Missing 'filename' attribute")
        filename = self.filename

        # Ensure the target directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filename)) or ".", exist_ok=True)

        # Write the data to a pickle file
        with open(filename, "wb") as fp:
            pickle.dump(data, fp)

# === BLOCK 5 (label=human, source_idx=line2270_human, name=reduce_activities) ===
def reduce_activities(stmts_in, **kwargs):
    """Reduce the activity types in a list of statements

    Parameters
    ----------
    stmts_in : list[indra.statements.Statement]
        A list of statements to reduce activity types in.
    save : Optional[str]
        The name of a pickle file to save the results (stmts_out) into.

    Returns
    -------
    stmts_out : list[indra.statements.Statement]
        A list of reduced activity statements.
    """
    logger.info('Reducing activities on %d statements...' % len(stmts_in))
    stmts_out = [deepcopy(st) for st in stmts_in]
    ml = MechLinker(stmts_out)
    ml.gather_explicit_activities()
    ml.reduce_activities()
    stmts_out = ml.statements
    dump_pkl = kwargs.get('save')
    if dump_pkl:
        dump_statements(stmts_out, dump_pkl)
    return stmts_out

# === BLOCK 6 (label=human, source_idx=line1351_human, name=read_raw_pressure) ===
def read_raw_pressure(self):
        """Reads the raw (uncompensated) pressure level from the sensor."""
        self.i2c.write8(BMP085_CONTROL, BMP085_READPRESSURECMD + (self._mode << 6))
        if self._mode == BMP085_ULTRALOWPOWER:
            time.sleep(0.005)
        elif self._mode == BMP085_HIGHRES:
            time.sleep(0.014)
        elif self._mode == BMP085_ULTRAHIGHRES:
            time.sleep(0.026)
        else:
            time.sleep(0.008)
        msb = self.i2c.read_U8(BMP085_PRESSUREDATA)
        lsb = self.i2c.read_U8(BMP085_PRESSUREDATA+1)
        xlsb = self.i2c.read_U8(BMP085_PRESSUREDATA+2)
        raw = ((msb << 16) + (lsb << 8) + xlsb) >> (8 - self._mode)
        self.logger.debug('Raw pressure 0x{0:04X} ({1})', raw & 0xFFFF, raw)
        return raw
