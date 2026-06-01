# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line292_human, name=time_cache) ===
def time_cache(time_add_setting):
    """ This decorator works as follows: Call it with a setting and after that
    use the function with a callable that returns the key.
    But: This function is only called if the key is not available. After a
    certain amount of time (`time_add_setting`) the cache is invalid.
    """
    def _temp(key_func):
        dct = {}
        _time_caches.append(dct)

        def wrapper(optional_callable, *args, **kwargs):
            key = key_func(*args, **kwargs)
            value = None
            if key in dct:
                expiry, value = dct[key]
                if expiry > time.time():
                    return value
            value = optional_callable()
            time_add = getattr(settings, time_add_setting)
            if key is not None:
                dct[key] = time.time() + time_add, value
            return value
        return wrapper
    return _temp

# === BLOCK 2 (label=lm, source_idx=line245_lm, name=handle_label) ===
def handle_label(self, label, **options):
        """
        Command handler.
        """
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', label):
            raise ValueError("Invalid label")
        if label in self.commands:
            raise ValueError("Label already in use")
        self.commands[label] = options

# === BLOCK 3 (label=human, source_idx=line938_human, name=_rc_context) ===
def _rc_context(rcparams):
    """
    Context manager that temporarily overrides the pyplot rcParams.
    """
    deprecated = ['text.latex.unicode', 'examples.directory']
    old_rcparams = {k: mpl.rcParams[k] for k in mpl.rcParams.keys()
                    if mpl_version < '3.0' or k not in deprecated}
    mpl.rcParams.clear()
    mpl.rcParams.update(dict(old_rcparams, **rcparams))
    try:
        yield
    finally:
        mpl.rcParams.clear()
        mpl.rcParams.update(old_rcparams)

# === BLOCK 4 (label=lm, source_idx=line780_lm, name=_python3_record_factory) ===
def _python3_record_factory(*args, **kwargs):
    """Python 3 approach to custom logging, using `logging.getLogRecord(...)`

    Inspireb by: https://docs.python.org/3/howto/logging-cookbook.html#customizing-logrecord

    :return: A log record augmented with the values required by LOG_FORMAT, as per `_update_record(...)`
    """
    record = logging.getLogRecord(*args, **kwargs)
    record.asctime2 = record.asctime[0:23]
    record.levelname2 = record.levelname.ljust(8)
    record.filename2 = record.filename.ljust(20)
    record.funcName2 = record.funcName.ljust(20)
    record.lineno2 = str(record.lineno).rjust(4)
    return record

# === BLOCK 5 (label=lm, source_idx=line4289_lm, name=fgrad_y) ===
def fgrad_y(self, y, return_precalc=False):
        """
        gradient of f w.r.t to y ([N x 1])

        :returns: Nx1 vector of derivatives, unless return_precalc is true, 
        then it also returns the precomputed stuff
        """
        precalc = self.precalc(y)
        grad = np.zeros(y.shape)
        for i in range(y.shape[0]):
            grad[i] = self.fgrad_y_i(y, i, precalc)

        if return_precalc:
            return grad, precalc
        else:
            return grad

# === BLOCK 6 (label=human, source_idx=line3000_human, name=next) ===
def next(self):
        """Returns the next item in the cursor."""
        if self._current_index < len(self._collection):
            value = self._collection[self._current_index]
            self._current_index += 1
            return value
        elif self._next_cursor:
            self.__fetch_next()
            return self.next()
        else:
            self._current_index = 0
            raise StopIteration
