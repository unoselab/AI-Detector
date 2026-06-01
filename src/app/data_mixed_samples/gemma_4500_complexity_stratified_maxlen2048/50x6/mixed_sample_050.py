# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1374_lm, name=_sorted_nicely) ===
def _sorted_nicely(self, l):
        """Return list sorted in the way that humans expect.

        :param l: iterable to be sorted
        :returns: sorted list
        """
        import re

        def alphanumeric_key(key):
            return [int(text) if text.isdigit() else text.lower()
                    for text in re.split('([0-9]+)', str(key))]

        return sorted(l, key=alphanumeric_key)

# === BLOCK 2 (label=human, source_idx=line3594_human, name=solve_limited) ===
def solve_limited(self, assumptions=[]):
        """
            Solve internal formula using given budgets for conflicts and
            propagations.
        """

        if self.minicard:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            self.status = pysolvers.minicard_solve_lim(self.minicard, assumptions)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return self.status

# === BLOCK 3 (label=lm, source_idx=line1661_lm, name=parse_case_snake_to_camel) ===
def parse_case_snake_to_camel(snake, upper_first=True):
	"""
	Convert a string from snake_case to CamelCase.

	:param str snake: The snake_case string to convert.
	:param bool upper_first: Whether or not to capitalize the first
		character of the string.
	:return: The CamelCase version of string.
	:rtype: str
	"""
	components = snake.split('_')
	words = [word.capitalize() for word in components if word]
	if not words:
		return ""
	if not upper_first:
		words[0] = words[0].lower()
	return "".join(words)

# === BLOCK 4 (label=human, source_idx=line532_human, name=console_check_for_keypress) ===
def console_check_for_keypress(flags: int = KEY_RELEASED) -> Key:
    """
    .. deprecated:: 9.3
        Use the :any:`tcod.event.get` function to check for events.
    """
    key = Key()
    lib.TCOD_console_check_for_keypress_wrapper(key.key_p, flags)
    return key

# === BLOCK 5 (label=lm, source_idx=line3313_lm, name=export) ===
def export(self, location):
        """
        Export the Bazaar repository at the url to the destination location
        """
        import os
        import subprocess

        if not os.path.exists(location):
            os.makedirs(location)

        try:
            subprocess.check_call(['bzr export', location])
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to export Bazaar repository: {e}")

# === BLOCK 6 (label=human, source_idx=line4031_human, name=_find_append_zero_crossings) ===
def _find_append_zero_crossings(x, y):
    r"""
    Find and interpolate zero crossings.

    Estimate the zero crossings of an x,y series and add estimated crossings to series,
    returning a sorted array with no duplicate values.

    Parameters
    ----------
    x : `pint.Quantity`
        x values of data
    y : `pint.Quantity`
        y values of data

    Returns
    -------
    x : `pint.Quantity`
        x values of data
    y : `pint.Quantity`
        y values of data

    """
    # Find and append crossings to the data
    crossings = find_intersections(x[1:], y[1:], np.zeros_like(y[1:]) * y.units)
    x = concatenate((x, crossings[0]))
    y = concatenate((y, crossings[1]))

    # Resort so that data are in order
    sort_idx = np.argsort(x)
    x = x[sort_idx]
    y = y[sort_idx]

    # Remove duplicate data points if there are any
    keep_idx = np.ediff1d(x, to_end=[1]) > 0
    x = x[keep_idx]
    y = y[keep_idx]
    return x, y
