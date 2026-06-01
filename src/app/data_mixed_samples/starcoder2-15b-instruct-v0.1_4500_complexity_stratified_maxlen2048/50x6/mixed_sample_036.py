# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2395_human, name=system_monitor_MM_threshold_marginal_threshold) ===
def system_monitor_MM_threshold_marginal_threshold(self, **kwargs):
        """Auto Generated Code
        """
        config = ET.Element("config")
        system_monitor = ET.SubElement(config, "system-monitor", xmlns="urn:brocade.com:mgmt:brocade-system-monitor")
        MM = ET.SubElement(system_monitor, "MM")
        threshold = ET.SubElement(MM, "threshold")
        marginal_threshold = ET.SubElement(threshold, "marginal-threshold")
        marginal_threshold.text = kwargs.pop('marginal_threshold')

        callback = kwargs.pop('callback', self._callback)
        return callback(config)

# === BLOCK 2 (label=lm, source_idx=line2993_lm, name=load) ===
def load(self, path=None, fatal=True, logger=None):
        """
        :param str|None path: Load this object from file with 'path' (default: self._path)
        :param bool|None fatal: Abort execution on failure if True
        :param callable|None logger: Logger to use
        """
        if path is None:
            path = self._path
        if logger is None:
            logger = self._logger
        try:
            with open(path, 'r') as f:
                data = f.read()
                self._data = data
        except Exception as e:
            if fatal:
                raise e
            else:
                logger.error(f'Failed to load data from {path}: {e}')

# === BLOCK 3 (label=human, source_idx=line600_human, name=_parse_openssl_req) ===
def _parse_openssl_req(csr_filename):
    """
    Parses openssl command line output, this is a workaround for M2Crypto's
    inability to get them from CSR objects.
    """
    if not salt.utils.path.which('openssl'):
        raise salt.exceptions.SaltInvocationError(
            'openssl binary not found in path'
        )
    cmd = ('openssl req -text -noout -in {0}'.format(csr_filename))

    output = __salt__['cmd.run_stdout'](cmd)

    output = re.sub(r': rsaEncryption', ':', output)
    output = re.sub(r'[0-9a-f]{2}:', '', output)

    return salt.utils.data.decode(salt.utils.yaml.safe_load(output))

# === BLOCK 4 (label=human, source_idx=line3344_human, name=_log) ===
def _log(self, fname, txt, prg=''):
        """
        logs an entry to fname along with standard date and user details
        """
        if os.sep not in fname:
            fname = self.log_folder + os.sep + fname
        delim = ','
        q = '"'
        dte = TodayAsString()
        usr = GetUserName()
        hst = GetHostName()
        i = self.session_id

        if prg == '':
            prg = 'cls_log.log' 
        logEntry = q + dte + q + delim + q + i + q + delim + q + usr + q + delim + q + hst + q + delim + q + prg + q + delim + q + txt + q + delim + '\n'
        with open(fname, "a", encoding='utf-8', errors='replace') as myfile:
            myfile.write(logEntry)

# === BLOCK 5 (label=lm, source_idx=line2520_lm, name=get_pks_for_filter) ===
def get_pks_for_filter(self, key, filter_type, value):
        """Extract the pks from the zset key for the given type and value

        For the parameters, see BaseRangeIndex.get_pks_for_filter
        """
        if filter_type == "range":
            start, end = value
            return self.redis.zrangebyscore(key, start, end)
        elif filter_type == "prefix":
            pattern = f"{value}*"
            return self.redis.zrangebylex(key, pattern, pattern)
        else:
            raise ValueError(f"Invalid filter type: {filter_type}")

# === BLOCK 6 (label=lm, source_idx=line800_lm, name=add_breakpoint) ===
def add_breakpoint(self, event_type, bp):
        """
        Adds a breakpoint which would trigger on `event_type`.

        :param event_type:  The event type to trigger on
        :param bp:          The breakpoint
        :return:            The created breakpoint.
        """
        if event_type not in self.breakpoints:
            self.breakpoints[event_type] = []
        self.breakpoints[event_type].append(bp)
        return bp
