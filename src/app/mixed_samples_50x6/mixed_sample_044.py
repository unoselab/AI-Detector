# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1813_lm, name=from_dict) ===
def from_dict(cls, copula_dict):
        """Set attributes with provided values."""
        obj = cls()
        for key, value in copula_dict.items():
            setattr(obj, key, value)
        return obj

# === BLOCK 2 (label=lm, source_idx=line862_lm, name=create) ===
def create(cls, fqdn, duration, owner, admin, tech, bill, nameserver,
               extra_parameter, background):
        """Create a domain."""
        return cls(fqdn, duration, owner, admin, tech, bill, nameserver,
               extra_parameter, background)

# === BLOCK 3 (label=human, source_idx=line2560_human, name=percentile) ===
def percentile(self, percentile):
        """Return bin center nearest to percentile"""
        return self.bin_centers[np.argmin(np.abs(self.cumulative_density * 100 - percentile))]

# === BLOCK 4 (label=human, source_idx=line130_human, name=load_class) ===
def load_class(module_name, class_name):
    """Return class object specified by module name and class name.

    Return None if module failed to be imported.

    :param module_name: string module name
    :param class_name: string class name
    """
    try:
        plugmod = import_module(module_name)
    except Exception as exc:
        warn("Importing built-in plugin %s.%s raised an exception: %r" %
             (module_name, class_name, repr(exc)), ImportWarning)
        return None
    else:
        return getattr(plugmod, class_name)

# === BLOCK 5 (label=human, source_idx=line2179_human, name=checkargs) ===
def checkargs(self, lineno, command, args):
		"""
		Check if the arguments fit the requirements of the command.

		Raises ArgumentError_, if an argument does not fit.
		"""
		for wanted, arg in zip(command.argtypes(), args):
			wanted = wanted.type_
			if(wanted == "register" and (not arg in self.register)):
				raise ArgumentError("[line {}]: Command '{}' wants argument of type register, but {} is not a register".format(lineno, command.mnemonic(), arg))
			if(wanted == "const" and (arg in self.register)):
				raise ArgumentError("[line {}]: Command '{}' wants argument of type const, but {} is a register.".format(lineno, command.mnemonic(), arg))

# === BLOCK 6 (label=lm, source_idx=line2763_lm, name=_can_hold_element) ===
def _can_hold_element(self, element):
        """ require the same dtype as ourselves """
        return element.dtype == self.dtype
