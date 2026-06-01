# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line7858_human, name=get_ordered_options) ===
def get_ordered_options(self, hidden=False):
        """
        :param hidden: whether to return hidden option
        :type hidden: bool
        :returns: **ordered** list of options pre-serialised (as_dict)
        :rtype: list `[opt_dict, ...]`
        """
        return [opt.as_dict() for opt in self.options.values() \
                                            if hidden or (not opt.hidden)]

# === BLOCK 2 (label=lm, source_idx=line1139_lm, name=to_rectangular) ===
def to_rectangular(image):
    """Transform image coordinates to rectangular.

    The image is transformed so that it is unwrapped from a point in the
    centre. Circles or segments of circles become vertical straight lines,
    radial lines become horizontal lines.
    """
    image = image.copy()
    image.transform_to_rectangular()
    return image

# === BLOCK 3 (label=lm, source_idx=line247_lm, name=_reflect_all) ===
def _reflect_all(exclude_tables=None, admin=None, read_only=False, schema=None):
    """Register all tables in the given database as services.

    :param list exclude_tables: A list of tables to exclude from the API
                                service
    """
    from . import api
    from . import models
    from . import admin

    if exclude_tables is None:
        exclude_tables = []

    if schema is None:
        schema = api.schema

    for table in models.db.metadata.sorted_tables:
        if table.name in exclude_tables:
            continue

        if read_only:
            api.read_only(table)
        else:
            api.service(table)

    if admin is not None:
        admin.init_app(app)

    return api

# === BLOCK 4 (label=human, source_idx=line775_human, name=get_unpatched_class) ===
def get_unpatched_class(cls):
    """Protect against re-patching the distutils if reloaded

    Also ensures that no other distutils extension monkeypatched the distutils
    first.
    """
    external_bases = (
        cls
        for cls in _get_mro(cls)
        if not cls.__module__.startswith('setuptools')
    )
    base = next(external_bases)
    if not base.__module__.startswith('distutils'):
        msg = "distutils has already been patched by %r" % cls
        raise AssertionError(msg)
    return base

# === BLOCK 5 (label=human, source_idx=line6216_human, name=save_state_regularly) ===
def save_state_regularly(self, fname, frequency=600):
        """
        Save the state of node with a given regularity to the given
        filename.

        Args:
            fname: File name to save retularly to
            frequency: Frequency in seconds that the state should be saved.
                        By default, 10 minutes.
        """
        self.save_state(fname)
        loop = asyncio.get_event_loop()
        self.save_state_loop = loop.call_later(frequency,
                                               self.save_state_regularly,
                                               fname,
                                               frequency)

# === BLOCK 6 (label=lm, source_idx=line195_lm, name=forget) ===
def forget(self):
        """
        Reset _observed events. Remove self from observers.
        :return: Nothing
        """
        for key in self._observed:
            self._observed[key].remove(self)
        self._observed = {}
