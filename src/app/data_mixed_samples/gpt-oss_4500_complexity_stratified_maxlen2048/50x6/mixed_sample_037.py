# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line6946_human, name=get) ===
def get(self, wrap_exception=False):
        """
        Return the return value of this Attempt instance or raise an Exception.
        If wrap_exception is true, this Attempt is wrapped inside of a
        RetryError before being raised.
        """
        if self.has_exception:
            if wrap_exception:
                raise RetryError(self)
            else:
                six.reraise(self.value[0], self.value[1], self.value[2])
        else:
            return self.value

# === BLOCK 2 (label=lm, source_idx=line1386_lm, name=create_ssh_config) ===
def create_ssh_config(remote_user='root', name='Auto Generated SSH Key',
                      file_name='fabricbolt_private.key', email='deployments@fabricbolt.io', public_key_text=None,
                      private_key_text=None):
    """Create SSH Key"""

# === BLOCK 3 (label=lm, source_idx=line1034_lm, name=probe_services) ===
def probe_services(self, handle, conn_id, callback):
        """Given a connected device, probe for its GATT services and characteristics

        Args:
            handle (int): a handle to the connection on the BLED112 dongle
            conn_id (int): a unique identifier for this connection on the DeviceManager
                that owns this adapter.
            callback (callable): Callback to be called when this procedure finishes
        """

# === BLOCK 4 (label=lm, source_idx=line4425_lm, name=count) ===
def count(self, axis='major'):
        """
        Return number of observations over requested axis.

        Parameters
        ----------
        axis : {'items', 'major', 'minor'} or {0, 1, 2}

        Returns
        -------
        count : DataFrame
        """

# === BLOCK 5 (label=human, source_idx=line3786_human, name=compare_bpdu_info) ===
def compare_bpdu_info(my_priority, my_times, rcv_priority, rcv_times):
        """ Check received BPDU is superior to currently held BPDU
             by the following comparison.
             - root bridge ID value
             - root path cost
             - designated bridge ID value
             - designated port ID value
             - times """
        if my_priority is None:
            result = SUPERIOR
        else:
            result = Stp._cmp_value(rcv_priority.root_id.value,
                                    my_priority.root_id.value)
            if not result:
                result = Stp.compare_root_path(
                    rcv_priority.root_path_cost,
                    my_priority.root_path_cost,
                    rcv_priority.designated_bridge_id.value,
                    my_priority.designated_bridge_id.value,
                    rcv_priority.designated_port_id.value,
                    my_priority.designated_port_id.value)
                if not result:
                    result1 = Stp._cmp_value(
                        rcv_priority.designated_bridge_id.value,
                        mac.haddr_to_int(
                            my_priority.designated_bridge_id.mac_addr))
                    result2 = Stp._cmp_value(
                        rcv_priority.designated_port_id.value,
                        my_priority.designated_port_id.port_no)
                    if not result1 and not result2:
                        result = SUPERIOR
                    else:
                        result = Stp._cmp_obj(rcv_times, my_times)
        return result

# === BLOCK 6 (label=human, source_idx=line5036_human, name=_parse_hunk_line) ===
def _parse_hunk_line(self, line):
        """
        Given a hunk line in `git diff` output, return the line number
        at the start of the hunk.  A hunk is a segment of code that
        contains changes.

        The format of the hunk line is:

            @@ -k,l +n,m @@ TEXT

        where `k,l` represent the start line and length before the changes
        and `n,m` represent the start line and length after the changes.

        `git diff` will sometimes put a code excerpt from within the hunk
        in the `TEXT` section of the line.
        """
        # Split the line at the @@ terminators (start and end of the line)
        components = line.split('@@')

        # The first component should be an empty string, because
        # the line starts with '@@'.  The second component should
        # be the hunk information, and any additional components
        # are excerpts from the code.
        if len(components) >= 2:

            hunk_info = components[1]
            groups = self.HUNK_LINE_RE.findall(hunk_info)

            if len(groups) == 1:

                try:
                    return int(groups[0])

                except ValueError:
                    msg = "Could not parse '{}' as a line number".format(groups[0])
                    raise GitDiffError(msg)

            else:
                msg = "Could not find start of hunk in line '{}'".format(line)
                raise GitDiffError(msg)

        else:
            msg = "Could not parse hunk in line '{}'".format(line)
            raise GitDiffError(msg)
