# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line447_lm, name=validate_set_ops) ===
def validate_set_ops(df, other):
    """
    Helper function to ensure that DataFrames are valid for set operations.
    Columns must be the same name in the same order, and indices must be of the
    same dimension with the same names.
    """
    if not df.columns.equals(other.columns):
        raise ValueError("Columns must be the same name in the same order")
    if not df.index.equals(other.index):
        raise ValueError("Indices must be of the same dimension with the same names")

# === BLOCK 2 (label=human, source_idx=line1915_human, name=thread_debug) ===
def thread_debug(self, *args, **kwargs):
        """
        Wrap debug to include thread information
        """
        if 'module' not in kwargs:
            kwargs['module'] = "Monitor"
        if kwargs['module'] != 'Monitor' and self.do_DEBUG(module='Monitor'):
            self.debug[kwargs['module']] = True
        if not self.do_DEBUG(module=kwargs['module']):
            return
        thread_id = threading.current_thread().name
        key = "[" + thread_id + "] " + kwargs['module']
        if not self.debug.get(key):
            self.debug[key] = True
        kwargs['module'] = key
        self.DEBUG(*args, **kwargs)

# === BLOCK 3 (label=human, source_idx=line906_human, name=get_single_outfile) ===
def get_single_outfile (directory, archive, extension=""):
    """Get output filename if archive is in a single file format like gzip."""
    outfile = os.path.join(directory, stripext(archive))
    if os.path.exists(outfile + extension):
        # prevent overwriting existing files
        i = 1
        newfile = "%s%d" % (outfile, i)
        while os.path.exists(newfile + extension):
            newfile = "%s%d" % (outfile, i)
            i += 1
        outfile = newfile
    return outfile + extension

# === BLOCK 4 (label=lm, source_idx=line35_lm, name=create) ===
def create(self, name, description, data_source_type,
               url, credential_user=None, credential_pass=None,
               is_public=None, is_protected=None, s3_credentials=None):
        """Create a Data Source."""
        data_source = Data_Source(name, description, data_source_type,
                                   url, credential_user, credential_pass,
                                   is_public, is_protected, s3_credentials)
        self.data_sources.append(data_source)
        return data_source

# === BLOCK 5 (label=lm, source_idx=line4958_lm, name=filter_by_col) ===
def filter_by_col(self, column_names):
        """filters sheet/table by columns (input is column header)

        The routine returns the serial numbers with values>1 in the selected
        columns.

        Args:
            column_names (list): the column headers.

        Returns:
            pandas.DataFrame
        """
        return self.df.loc[self.df[column_names] > 1].index.tolist()

# === BLOCK 6 (label=human, source_idx=line4594_human, name=print_func_call) ===
def print_func_call(ignore_first_arg=False, max_call_number=100):
    """ utility function to facilitate debug, it will print input args before
    function call, and print return value after function call

    usage:

        @print_func_call
        def some_func_to_be_debu():
            pass

    :param ignore_first_arg: whether print the first arg or not.
    useful when ignore the `self` parameter of an object method call
    """
    from functools import wraps

    def display(x):
        x = to_string(x)
        try:
            x.decode('ascii')
        except BaseException:
            return 'NON_PRINTABLE'
        return x

    local = {'call_number': 0}

    def inner(f):

        @wraps(f)
        def wrapper(*args, **kwargs):
            local['call_number'] += 1
            tmp_args = args[1:] if ignore_first_arg and len(args) else args
            this_call_number = local['call_number']
            print(('{0}#{1} args: {2}, {3}'.format(
                f.__name__,
                this_call_number,
                ', '.join([display(x) for x in tmp_args]),
                ', '.join(display(key) + '=' + to_string(value)
                          for key, value in kwargs.items())
            )))
            res = f(*args, **kwargs)
            print(('{0}#{1} return: {2}'.format(
                f.__name__,
                this_call_number,
                display(res))))

            if local['call_number'] > 100:
                raise Exception("Touch max call number!")
            return res
        return wrapper
    return inner
