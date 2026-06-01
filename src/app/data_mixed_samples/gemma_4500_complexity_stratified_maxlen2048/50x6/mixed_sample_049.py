# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line7409_human, name=extract_docstring) ===
def extract_docstring(filename):
    """ Extract a module-level docstring, if any
    """
    lines = file(filename).readlines()
    start_row = 0
    if lines[0].startswith('#!'):
        lines.pop(0)
        start_row = 1

    docstring = ''
    first_par = ''
    tokens = tokenize.generate_tokens(iter(lines).next)
    for tok_type, tok_content, _, (erow, _), _ in tokens:
        tok_type = token.tok_name[tok_type]
        if tok_type in ('NEWLINE', 'COMMENT', 'NL', 'INDENT', 'DEDENT'):
            continue
        elif tok_type == 'STRING':
            docstring = eval(tok_content)
            # If the docstring is formatted with several paragraphs, extract
            # the first one:
            paragraphs = '\n'.join(line.rstrip()
                              for line in docstring.split('\n')).split('\n\n')
            if len(paragraphs) > 0:
                first_par = paragraphs[0]
        break
    end_row = erow + 1 + start_row
    if lines and lines[end_row - 2] == 'print(__doc__)\n':
        end_row += 1
    return docstring, first_par, end_row

# === BLOCK 2 (label=lm, source_idx=line2246_lm, name=start) ===
def start(self):
        """Begin executing tasks."""
        self._running = True
        while self._running and self._tasks:
            task = self._tasks.pop(0)
            task.execute()

# === BLOCK 3 (label=human, source_idx=line7785_human, name=update) ===
def update(self, content):
        """Enumerates the bytes of the supplied bytearray and updates the CRC-64.
           No return value.
        """

        for byte in content:
            self._crc64 = (self._crc64 >> 8) ^ self._lookup_table[(self._crc64 & 0xff) ^ byte]

# === BLOCK 4 (label=human, source_idx=line3173_human, name=_get_fwl_billing_item) ===
def _get_fwl_billing_item(self, firewall_id, dedicated=False):
        """Retrieves the billing item of the firewall.

        :param int firewall_id: Firewall ID to get the billing item for
        :param bool dedicated: whether the firewall is dedicated or standard
        :returns: A dictionary of the firewall billing item.
        """

        mask = 'mask[id,billingItem[id]]'
        if dedicated:
            firewall_service = self.client['Network_Vlan_Firewall']
        else:
            firewall_service = self.client['Network_Component_Firewall']
        firewall = firewall_service.getObject(id=firewall_id, mask=mask)
        if firewall is None:
            raise exceptions.SoftLayerError(
                "Unable to find firewall %d" % firewall_id)
        if firewall.get('billingItem') is None:
            raise exceptions.SoftLayerError(
                "Unable to find billing item for firewall %d" % firewall_id)

        return firewall['billingItem']

# === BLOCK 5 (label=lm, source_idx=line5230_lm, name=is_pre_prepare_time_acceptable) ===
def is_pre_prepare_time_acceptable(self, pp: PrePrepare, sender: str) -> bool:
        """
        Returns True or False depending on the whether the time in PRE-PREPARE
        is acceptable. Can return True if time is not acceptable but sufficient
        PREPAREs are found to support the PRE-PREPARE
        :param pp:
        :return:
        """
        if pp.timestamp < self.current_time - self.max_clock_drift:
            return False
        if pp.timestamp > self.current_time + self.max_clock_drift:
            return False
        return True

# === BLOCK 6 (label=lm, source_idx=line7906_lm, name=exposure_preparation) ===
def exposure_preparation(self):
        """This function is doing the exposure preparation."""
        # Implementation for exposure preparation
        # This typically involves setting sensor parameters, 
        # clearing buffers, and triggering the shutter sequence.
        self.prepare_sensor()
        self.set_exposure_time(self.exposure_time)
        self.set_gain(self.gain)
        self.clear_frame_buffer()
        self.arm_trigger()
