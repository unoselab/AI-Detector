# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line5192_human, name=container_stop) ===
def container_stop(name, timeout=30, force=True, remote_addr=None,
                   cert=None, key=None, verify_cert=True):
    """
    Stop a container

    name :
        Name of the container to stop

    remote_addr :
        An URL to a remote Server, you also have to give cert and key if
        you provide remote_addr and its a TCP Address!

        Examples:
            https://myserver.lan:8443
            /var/lib/mysocket.sock

    cert :
        PEM Formatted SSL Certificate.

        Examples:
            ~/.config/lxc/client.crt

    key :
        PEM Formatted SSL Key.

        Examples:
            ~/.config/lxc/client.key

    verify_cert : True
        Wherever to verify the cert, this is by default True
        but in the most cases you want to set it off as LXD
        normaly uses self-signed certificates.
    """
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )
    container.stop(timeout, force, wait=True)
    return _pylxd_model_to_dict(container)

# === BLOCK 2 (label=lm, source_idx=line3047_lm, name=strtime) ===
def strtime (t, func=time.localtime):
    """Return ISO 8601 formatted time."""
    try:
        st = func(t)
    except TypeError:
        st = t
    return f"{st.tm_year:04d}-{st.tm_mon:02d}-{st.tm_mday:02d}T{st.tm_hour:02d}:{st.tm_min:02d}:{st.tm_sec:02d}"

# === BLOCK 3 (label=lm, source_idx=line4626_lm, name=lexical_parent) ===
def lexical_parent(self):
        """Return the lexical parent for this cursor."""
        if hasattr(self, '_cursor'):
            return getattr(self._cursor, 'lexical_parent', None)
        if hasattr(self, 'cursor'):
            return getattr(self.cursor, 'lexical_parent', None)
        raise AttributeError("No underlying cursor attribute found for lexical_parent")

# === BLOCK 4 (label=lm, source_idx=line5190_lm, name=choices) ===
def choices(self):
        """
        When it's time to get the choices, if it was a lazy then figure it out
        now and memoize the result.
        """
        if callable(self._choices):
            result = self._choices()
            self._choices = result
            return result
        return self._choices

# === BLOCK 5 (label=human, source_idx=line4606_human, name=expand_array) ===
def expand_array(self, array_name):
        """Expand variables and return a set of keywords.

        :param str array_name: The name of the array to expand.

        :return list: The final array contents.

        Warning is issued when exceptions occur."""
        ret = self.master._array[array_name] if array_name in self.master._array else []
        try:
            ret = self.do_expand_array(array_name)
        except Exception as e:
            self.warn("Error expanding array '%s': %s" % (array_name, str(e)))
        return ret

# === BLOCK 6 (label=human, source_idx=line2470_human, name=create_filter) ===
def create_filter(extended, from_id, to_id, rtr_only, rtr_too):
        """
        Calculates AMR and ACR using CAN-ID as parameter.

        :param bool extended:
            if True parameters from_id and to_id contains 29-bit CAN-ID

        :param int from_id:
            first CAN-ID which should be received

        :param int to_id:
            last CAN-ID which should be received

        :param bool rtr_only:
            if True only RTR-Messages should be received, and rtr_too will be ignored

        :param bool rtr_too:
            if True CAN data frames and RTR-Messages should be received

        :return: Returns list with one filter containing a "can_id", a "can_mask" and "extended" key.
        """
        return [{
            "can_id": Ucan.calculate_acr(extended, from_id, to_id, rtr_only, rtr_too),
            "can_mask": Ucan.calculate_amr(extended, from_id, to_id, rtr_only, rtr_too),
            "extended": extended
        }]
