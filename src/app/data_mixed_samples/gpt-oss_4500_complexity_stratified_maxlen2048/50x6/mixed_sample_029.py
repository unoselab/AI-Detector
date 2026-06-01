# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1483_human, name=from_dict) ===
def from_dict(cls, d, fmt=None):
        """
        Reconstitute a Structure object from a dict representation of Structure
        created using as_dict().

        Args:
            d (dict): Dict representation of structure.

        Returns:
            Structure object
        """
        if fmt == "abivars":
            from pymatgen.io.abinit.abiobjects import structure_from_abivars
            return structure_from_abivars(cls=cls, **d)

        lattice = Lattice.from_dict(d["lattice"])
        sites = [PeriodicSite.from_dict(sd, lattice) for sd in d["sites"]]
        charge = d.get("charge", None)
        return cls.from_sites(sites, charge=charge)

# === BLOCK 2 (label=lm, source_idx=line1551_lm, name=carry_in) ===
def carry_in(value, carry, base):
        """
        Add a carry digit to a number represented by ``value``.

        :param value: the value
        :type value: list of int
        :param int carry: the carry digit (>= 0)
        :param int base: the base (>= 2)

        :returns: carry-out and result
        :rtype: tuple of int * (list of int)

	Complexity: O(len(value))
        """

# === BLOCK 3 (label=human, source_idx=line6096_human, name=absent) ===
def absent(name, poll=5, timeout=60, profile=None):
    """
    Ensure that the named stack is absent

    name
        The name of the stack to remove

    poll
        Poll(in sec.) and report events until stack complete

    timeout
        Stack creation timeout in minutes

    profile
        Profile to use

    """
    log.debug('Absent with (%s, %s %s)', name, poll, profile)
    ret = {'name': None,
           'comment': '',
           'changes': {},
           'result': True}
    if not name:
        ret['result'] = False
        ret['comment'] = 'Name ist not valid'
        return ret

    ret['name'] = name,

    existing_stack = __salt__['heat.show_stack'](name, profile=profile)

    if not existing_stack['result']:
        ret['result'] = True
        ret['comment'] = 'Stack not exist'
        return ret
    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Stack {0} is set to be removed'.format(name)
        return ret

    stack = __salt__['heat.delete_stack'](name=name, poll=poll,
                                          timeout=timeout, profile=profile)

    ret['result'] = stack['result']
    ret['comment'] = stack['comment']
    ret['changes']['stack_name'] = name
    ret['changes']['comment'] = 'Delete stack'
    return ret

# === BLOCK 4 (label=lm, source_idx=line5678_lm, name=set_api_key_from_file) ===
def set_api_key_from_file(path, set_global=True):
    """Set the global api_key from a file path."""
    from pathlib import Path

    file_path = Path(path)
    key = file_path.read_text(encoding="utf-8").strip()
    if set_global:
        globals()["api_key"] = key
    return key

# === BLOCK 5 (label=lm, source_idx=line3961_lm, name=decorator) ===
def decorator(caller, _func=None):
    """decorator(caller) converts a caller function into a decorator"""
    if _func is None:
        return lambda f: decorator(caller, f)
    import functools
    @functools.wraps(_func)
    def wrapper(*args, **kwargs):
        return caller(_func, *args, **kwargs)
    return wrapper

# === BLOCK 6 (label=human, source_idx=line2893_human, name=hour) ===
def hour(self, value=None):
        """Corresponds to IDD Field `hour`

        Args:
            value (int): value for IDD Field `hour`
                value >= 1
                value <= 24
                if `value` is None it will not be checked against the
                specification and is assumed to be a missing value

        Raises:
            ValueError: if `value` is not a valid value

        """
        if value is not None:
            try:
                value = int(value)
            except ValueError:
                raise ValueError('value {} need to be of type int '
                                 'for field `hour`'.format(value))
            if value < 1:
                raise ValueError('value need to be greater or equal 1 '
                                 'for field `hour`')
            if value > 24:
                raise ValueError('value need to be smaller 24 '
                                 'for field `hour`')

        self._hour = value
