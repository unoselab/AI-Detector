# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4489_human, name=add) ===
def add(self, key, val):
        """Adds a (name, value) pair, doesn't overwrite the value if it already
        exists.

        >>> headers = HTTPHeaderDict(foo='bar')
        >>> headers.add('Foo', 'baz')
        >>> headers['foo']
        'bar, baz'
        """
        key_lower = key.lower()
        new_vals = key, val
        # Keep the common case aka no item present as fast as possible
        vals = _dict_setdefault(self, key_lower, new_vals)
        if new_vals is not vals:
            # new_vals was not inserted, as there was a previous one
            if isinstance(vals, list):
                # If already several items got inserted, we have a list
                vals.append(val)
            else:
                # vals should be a tuple then, i.e. only one item so far
                # Need to convert the tuple to list for further extension
                _dict_setitem(self, key_lower, [vals[0], vals[1], val])

# === BLOCK 2 (label=lm, source_idx=line2184_lm, name=ip_to_array) ===
def ip_to_array(ipaddress):
    """Convert a string representing an IPv4 address to 4 bytes."""
    octets = ipaddress.split(".")
    return bytes([int(octet) for octet in octets])

# === BLOCK 3 (label=human, source_idx=line4835_human, name=readBoolean) ===
def readBoolean(self):
        """
        Read C{Boolean}.

        @raise ValueError: Error reading Boolean.
        @rtype: C{bool}
        @return: A Boolean value, C{True} if the byte
        is nonzero, C{False} otherwise.
        """
        byte = self.stream.read(1)

        if byte == '\x00':
            return False
        elif byte == '\x01':
            return True
        else:
            raise ValueError("Error reading boolean")

# === BLOCK 4 (label=human, source_idx=line4738_human, name=handle_input) ===
def handle_input(self, event):
        """Process the mouse event."""
        self.update_timeval()
        self.events = []
        code = self._get_event_type(event)

        # Deal with buttons
        self.handle_button(event, code)

        # Mouse wheel
        if code == 22:
            self.handle_scrollwheel(event)
        # Other relative mouse movements
        else:
            self.handle_relative(event)

        # Add in the absolute position of the mouse cursor
        self.handle_absolute(event)

        # End with a sync marker
        self.events.append(self.sync_marker(self.timeval))

        # We are done
        self.write_to_pipe(self.events)

# === BLOCK 5 (label=lm, source_idx=line3275_lm, name=create) ===
def create(configs):
    """Initializes the sniffer structures based on the JSON configuration. The
    expected keys are:

        * Type: A first-level type of sniffer. Planned to be 'local' for
            sniffers running on the local machine, or 'remote' for sniffers
            running remotely.
        * SubType: The specific sniffer type to be used.
        * Interface: The WLAN interface used to configure the sniffer.
        * BaseConfigs: A dictionary specifying baseline configurations of
            the sniffer. Configurations can be overridden when starting a
            capture. The keys must be one of the Sniffer.CONFIG_KEY_*
            values.
    """
    def __init__(self, type, subtype, interface, base_configs):
        self.type = type
        self.subtype = subtype
        self.interface = interface
        self.base_configs = base_configs

# === BLOCK 6 (label=lm, source_idx=line3897_lm, name=print_status) ===
def print_status(self, repo):
        """Print status
        """
        print(f"On branch {self.branch}")
        if self.is_dirty():
            print("Changes to be committed:")
            for change in self.changes:
                print(f"\t{change}")
            print("Changes not staged for commit:")
            for change in self.changes:
                print(f"\t{change}")
        else:
            print("nothing to commit, working tree clean")
