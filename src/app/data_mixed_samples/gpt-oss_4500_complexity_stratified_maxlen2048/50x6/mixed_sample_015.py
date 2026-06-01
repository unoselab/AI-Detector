# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2380_lm, name=set_defaults) ===
def set_defaults(self, address):
        """
        Set defaults

        If a message has different than low priority or NO_RTR set,
        then this method needs override in subclass

        :return: None
        """
        # Set default priority to low and disable RTR if not already set.
        # Supports both dict-like and object-like address containers.
        if isinstance(address, dict):
            address.setdefault('priority', 'low')
            address.setdefault('rtr', False)
        else:
            if not hasattr(address, 'priority'):
                setattr(address, 'priority', 'low')
            if not hasattr(address, 'rtr'):
                setattr(address, 'rtr', False)

# === BLOCK 2 (label=human, source_idx=line1899_human, name=findspan) ===
def findspan(self, *words):
        """Returns the span element which spans over the specified words or morphemes.

        See also:
            :meth:`Word.findspans`
        """

        for span in self.select(AbstractSpanAnnotation,None,True):
            if tuple(span.wrefs()) == words:
                return span
        raise NoSuchAnnotation

# === BLOCK 3 (label=lm, source_idx=line4712_lm, name=hide_virtual_ip_holder_chassis_virtual_ipv6) ===
def hide_virtual_ip_holder_chassis_virtual_ipv6(self, **kwargs):
        """Auto Generated Code
        """
        if hasattr(self, '_request'):
            return self._request('POST', '/hideVirtualIpHolderChassisVirtualIpv6', json=kwargs)
        return kwargs

# === BLOCK 4 (label=human, source_idx=line3316_human, name=find_schema) ===
def find_schema(schema_dir, obj_type):
    """Search the `schema_dir` directory for a schema called `obj_type`.json.
    Return the file path of the first match it finds.
    """
    schema_filename = obj_type + '.json'

    for root, dirnames, filenames in os.walk(schema_dir):
        if schema_filename in filenames:
            return os.path.join(root, schema_filename)

# === BLOCK 5 (label=human, source_idx=line4572_human, name=peek_pointers_in_data) ===
def peek_pointers_in_data(self, data, peekSize = 16, peekStep = 1):
        """
        Tries to guess which values in the given data are valid pointers,
        and reads some data from them.

        @see: L{peek}

        @type  data: str
        @param data: Binary data to find pointers in.

        @type  peekSize: int
        @param peekSize: Number of bytes to read from each pointer found.

        @type  peekStep: int
        @param peekStep: Expected data alignment.
            Tipically you specify 1 when data alignment is unknown,
            or 4 when you expect data to be DWORD aligned.
            Any other value may be specified.

        @rtype:  dict( str S{->} str )
        @return: Dictionary mapping stack offsets to the data they point to.
        """
        result = dict()
        ptrSize = win32.sizeof(win32.LPVOID)
        if ptrSize == 4:
            ptrFmt = '<L'
        else:
            ptrFmt = '<Q'
        if len(data) > 0:
            for i in compat.xrange(0, len(data), peekStep):
                packed          = data[i:i+ptrSize]
                if len(packed) == ptrSize:
                    address     = struct.unpack(ptrFmt, packed)[0]
##                    if not address & (~0xFFFF): continue
                    peek_data   = self.peek(address, peekSize)
                    if peek_data:
                        result[i] = peek_data
        return result

# === BLOCK 6 (label=lm, source_idx=line1020_lm, name=reload_inasafe_modules) ===
def reload_inasafe_modules(module_name=None):
    """Reload python modules.

    :param module_name: Specific module name.
    :type module_name: str
    """
    import sys
    import importlib

    reloaded = []

    def _reload(mod):
        try:
            importlib.reload(mod)
            return True
        except Exception:
            return False

    if module_name:
        # Reload the specified module if it exists
        mod = sys.modules.get(module_name)
        if mod and _reload(mod):
            reloaded.append(module_name)
        # Reload any submodules
        prefix = module_name + "."
        for name, mod in list(sys.modules.items()):
            if name.startswith(prefix):
                if _reload(mod):
                    reloaded.append(name)
    else:
        # Reload all modules that start with 'inasafe'
        prefix = "inasafe"
        for name, mod in list(sys.modules.items()):
            if name.startswith(prefix):
                if _reload(mod):
                    reloaded.append(name)

    return reloaded
