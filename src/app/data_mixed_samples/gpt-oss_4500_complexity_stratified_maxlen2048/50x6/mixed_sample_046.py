# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1835_human, name=push_irq_registers) ===
def push_irq_registers(self):
        """
        push PC, U, Y, X, DP, B, A, CC on System stack pointer
        """
        self.cycles += 1
        self.push_word(self.system_stack_pointer, self.program_counter.value) # PC
        self.push_word(self.system_stack_pointer, self.user_stack_pointer.value) # U
        self.push_word(self.system_stack_pointer, self.index_y.value) # Y
        self.push_word(self.system_stack_pointer, self.index_x.value) # X
        self.push_byte(self.system_stack_pointer, self.direct_page.value) # DP
        self.push_byte(self.system_stack_pointer, self.accu_b.value) # B
        self.push_byte(self.system_stack_pointer, self.accu_a.value) # A
        self.push_byte(self.system_stack_pointer, self.get_cc_value())

# === BLOCK 2 (label=lm, source_idx=line447_lm, name=can_add_lv_load_area) ===
def can_add_lv_load_area(self, node):
        # TODO: check docstring
        """Sums up peak load of LV stations 

        That is, total peak load for satellite string

        Args
        ----
        node: GridDing0
            Descr

        Returns
        -------
        bool
            True if ????

        """
        total_peak = 0.0
        for station in getattr(node, "lv_stations", []):
            total_peak += float(getattr(station, "peak_load", 0.0) or 0.0)

        max_allowed = getattr(self, "max_lv_load", None)
        if max_allowed is not None:
            return total_peak <= float(max_allowed)
        return total_peak > 0.0

# === BLOCK 3 (label=human, source_idx=line4470_human, name=add_item) ===
def add_item(self, item):
        """Add single command line flag

        Arguments:
            name (:obj:`str`): Name of flag used in command line
            flag_type (:py:class:`snap_plugin.v1.plugin.FlagType`):
                Indication if flag should store value or is simple bool flag
            description (:obj:`str`): Flag description used in command line
            default (:obj:`object`, optional): Optional default value for flag

        Raises:
            TypeError: Provided wrong arguments or arguments of wrong types, method will raise TypeError

        """
        if not(isinstance(item.name, basestring) and isinstance(item.description, basestring)):
            raise TypeError("Name and description should be strings, are of type {} and {}"
                            .format(type(item.name), type(item.description)))
        if not(isinstance(item.flag_type, FlagType)):
            raise TypeError("Flag type should be of type FlagType, is of {}".format(type(item.flag_type)))

        if item.name not in self._flags:
            if item.default is not None:
                if item.default is not False:
                    item.description = item.description + " (default: %(default)s)"
                self._flags[item.name] = item
            else:
                self._flags[item.name] = item

# === BLOCK 4 (label=lm, source_idx=line6165_lm, name=get_vlan) ===
def get_vlan(self, *args, **kwargs):
        """
        Get the VLAN from this PhysicalInterface.
        Use args if you want to specify only the VLAN id. Otherwise
        you can specify a valid attribute for the VLAN sub interface
        such as `address` for example::

            >>> vlan = itf.vlan_interface.get_vlan(4)
            >>> vlan
            Layer3PhysicalInterfaceVlan(name=VLAN 3.4)
            >>> vlan.addresses
            [(u'32.32.32.36', u'32.32.32.0/24', u'3.4'), (u'32.32.32.33', u'32.32.32.0/24', u'3.4')]

        :param int args: args are translated to vlan_id=args[0]
        :param kwargs: key value for sub interface
        :raises InterfaceNotFound: VLAN interface could not be found
        :rtype: VlanInterface
        """

# === BLOCK 5 (label=lm, source_idx=line2510_lm, name=load_swagger_spec) ===
def load_swagger_spec(self, filepath=None):
        """
        Loads the origin_spec from a local JSON file.  If `filepath`
        is not provided, then the class `file_spec` format will be used
        to create the file-path value.
        """
        import json
        import os

        # Determine the file path to load
        if filepath is None:
            # Use the class's `file_spec` attribute if available
            if hasattr(self, "file_spec"):
                # If `file_spec` is callable (e.g., a lambda) use it, otherwise treat as a string
                file_spec = self.file_spec
                if callable(file_spec):
                    filepath = file_spec()
                else:
                    filepath = str(file_spec)
            else:
                raise ValueError("No filepath provided and `self.file_spec` is undefined.")
        else:
            filepath = str(filepath)

        # Expand user and environment variables, and make the path absolute
        filepath = os.path.abspath(os.path.expanduser(os.path.expandvars(filepath)))

        # Load the JSON content
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                spec = json.load(f)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Swagger spec file not found: {filepath}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in swagger spec file: {filepath}") from exc

        # Store the loaded spec on the instance
        self.origin_spec = spec
        return spec

# === BLOCK 6 (label=human, source_idx=line430_human, name=get_version_from_dirname) ===
def get_version_from_dirname(name, parent):
    """Extracted sdist"""
    parent = parent.resolve()

    re_dirname = re.compile(f"{name}-{RE_VERSION}$")
    if not re_dirname.match(parent.name):
        return None

    return Version.parse(parent.name[len(name) + 1 :])
