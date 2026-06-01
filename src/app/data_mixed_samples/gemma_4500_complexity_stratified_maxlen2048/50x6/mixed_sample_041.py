# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line6044_human, name=happybirthday) ===
def happybirthday(person):
    """
    Sing Happy Birthday
    """
    print('Happy Birthday To You')
    time.sleep(2)
    print('Happy Birthday To You')
    time.sleep(2)
    print('Happy Birthday Dear ' + str(person[0].upper()) + str(person[1:]))
    time.sleep(2)
    print('Happy Birthday To You')

# === BLOCK 2 (label=human, source_idx=line4098_human, name=client_port) ===
def client_port(self):
        """Client connection's TCP port."""
        address = self._client.getpeername()
        if isinstance(address, tuple):
            return address[1]

        # Maybe a Unix domain socket connection.
        return 0

# === BLOCK 3 (label=lm, source_idx=line33_lm, name=parse) ===
def parse(text):
        """Try to parse into a date.

        Return:
            tuple (year, month, date) if successful; otherwise None.
        """
        import datetime
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%B %d, %Y", "%d %B %Y"):
            try:
                dt = datetime.datetime.strptime(text, fmt)
                return (dt.year, dt.month, dt.day)
            except ValueError:
                continue
        return None

# === BLOCK 4 (label=lm, source_idx=line2726_lm, name=missing_optional_tagfiles) ===
def missing_optional_tagfiles(self):
        """
        From v0.97 we need to validate any tagfiles listed
        in the optional tagmanifest(s). As there is no mandatory
        directory structure for additional tagfiles we can
        only check for entries with missing files (not missing
        entries for existing files).
        """
        missing = []
        for manifest in self.get_optional_tagmanifests():
            for tagfile in manifest.get_tagfiles():
                if not tagfile.exists():
                    missing.append(tagfile)
        return missing

# === BLOCK 5 (label=human, source_idx=line5230_human, name=is_pre_prepare_time_acceptable) ===
def is_pre_prepare_time_acceptable(self, pp: PrePrepare, sender: str) -> bool:
        """
        Returns True or False depending on the whether the time in PRE-PREPARE
        is acceptable. Can return True if time is not acceptable but sufficient
        PREPAREs are found to support the PRE-PREPARE
        :param pp:
        :return:
        """
        key = (pp.viewNo, pp.ppSeqNo)
        if key in self.requested_pre_prepares:
            # Special case for requested PrePrepares
            return True
        correct = self.is_pre_prepare_time_correct(pp, sender)
        if not correct:
            if key in self.pre_prepares_stashed_for_incorrect_time and \
                    self.pre_prepares_stashed_for_incorrect_time[key][-1]:
                self.logger.debug('{} marking time as correct for {}'.format(self, pp))
                correct = True
            else:
                self.logger.warning('{} found {} to have incorrect time.'.format(self, pp))
        return correct

# === BLOCK 6 (label=lm, source_idx=line4621_lm, name=_update_parsed_node_info) ===
def _update_parsed_node_info(self, parsed_node, config):
        """Given the SourceConfig used for parsing and the parsed node,
        generate and set the true values to use, overriding the temporary parse
        values set in _build_intermediate_parsed_node.
        """
        for key, value in parsed_node.items():
            if key in config:
                parsed_node[key] = config[key]
            elif isinstance(value, dict):
                self._update_parsed_node_info(value, config)
