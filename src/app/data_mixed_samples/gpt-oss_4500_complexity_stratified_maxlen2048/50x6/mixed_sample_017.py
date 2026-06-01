# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1911_lm, name=update) ===
def update(self):
        """Update |C1| based on :math:`c_1 = \\frac{Damp}{1+Damp}`.

        Examples:

            The first examples show the calculated value of |C1| for
            the lowest possible value of |Lag|, the lowest possible value,
            and an intermediate value:

            >>> from hydpy.models.hstream import *
            >>> parameterstep('1d')
            >>> damp(0.0)
            >>> derived.c1.update()
            >>> derived.c1
            c1(0.0)
            >>> damp(1.0)
            >>> derived.c1.update()
            >>> derived.c1
            c1(0.5)
            >>> damp(0.25)
            >>> derived.c1.update()
            >>> derived.c1
            c1(0.2)

            For to low and to high values of |Lag|, clipping is performed:
            >>> damp.value = -0.1
            >>> derived.c1.update()
            >>> derived.c1
            c1(0.0)
            >>> damp.value = 1.1
            >>> derived.c1.update()
            >>> derived.c1
            c1(0.5)
        """

# === BLOCK 2 (label=lm, source_idx=line410_lm, name=load_entry_point_group) ===
def load_entry_point_group(self, entry_point_group):
        """Load actions from an entry point group.

        :param entry_point_group: The entrypoint group name to load plugins.
        """
        import importlib.metadata as _metadata
        loaded = []
        try:
            eps = _metadata.entry_points()
            if hasattr(eps, "select"):
                eps = eps.select(group=entry_point_group)
            else:
                eps = eps.get(entry_point_group, [])
        except Exception:
            return loaded
        for ep in eps:
            try:
                obj = ep.load()
                loaded.append(obj)
            except Exception:
                continue
        if not hasattr(self, "_entry_point_actions"):
            self._entry_point_actions = {}
        self._entry_point_actions[entry_point_group] = loaded
        return

# === BLOCK 3 (label=lm, source_idx=line120_lm, name=print_change) ===
def print_change(self, symbol, typ, changes=None, document=None, **kwargs):
        """Print out a change"""
        parts = [f"Symbol: {symbol}", f"Type: {typ}"]
        if changes is not None:
            parts.append(f"Changes: {changes}")
        if document is not None:
            parts.append(f"Document: {document}")
        for key, value in kwargs.items():
            parts.append(f"{key}: {value}")
        print("; ".join(parts))

# === BLOCK 4 (label=human, source_idx=line5643_human, name=get_hdrgos_g_usrgos) ===
def get_hdrgos_g_usrgos(self, usrgos):
        """Return hdrgos which contain the usrgos."""
        hdrgos_for_usrgos = set()
        hdrgos_all = self.get_hdrgos()
        usrgo2hdrgo = self.get_usrgo2hdrgo()
        for usrgo in usrgos:
            if usrgo in hdrgos_all:
                hdrgos_for_usrgos.add(usrgo)
                continue
            hdrgo_cur = usrgo2hdrgo.get(usrgo, None)
            if hdrgo_cur is not None:
                hdrgos_for_usrgos.add(hdrgo_cur)
        return hdrgos_for_usrgos

# === BLOCK 5 (label=human, source_idx=line3690_human, name=generate_data) ===
def generate_data(self, *args, **kwargs):
    """Generates data for each problem."""
    for p in self.problems:
      p.generate_data(*args, **kwargs)

# === BLOCK 6 (label=human, source_idx=line4921_human, name=get_next_non_summer_term) ===
def get_next_non_summer_term(term):
    """
    Return the Term object for the quarter after
    as the given term (skip the summer quarter)
    """
    next_term = get_term_after(term)
    if next_term.is_summer_quarter():
        return get_next_autumn_term(next_term)
    return next_term
