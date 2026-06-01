# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3203_lm, name=del_ns) ===
def del_ns(self, namespace):
        """ will remove a namespace ref from the manager. either Arg is
        optional.

        args:
            namespace: prefix, string or Namespace() to remove
        """
        if isinstance(namespace, Namespace):
            namespace = namespace.prefix
        if namespace in self.namespaces:
            del self.namespaces[namespace]

# === BLOCK 2 (label=human, source_idx=line6000_human, name=read_config_file) ===
def read_config_file(libname):
    """
    Extract library locations from a configuration file.

    Parameters
    ----------
    libname : str
        One of either 'openjp2' or 'openjpeg'

    Returns
    -------
    path : None or str
        None if no location is specified, otherwise a path to the library
    """
    filename = glymurrc_fname()
    if filename is None:
        # There's no library file path to return in this case.
        return None

    # Read the configuration file for the library location.
    parser = ConfigParser()
    parser.read(filename)
    try:
        path = parser.get('library', libname)
    except (NoOptionError, NoSectionError):
        path = None
    return path

# === BLOCK 3 (label=human, source_idx=line5422_human, name=create_ui) ===
def create_ui(self):
        """
        .. versionchanged:: 0.21.2
            Load the builder configuration file using :func:`pkgutil.getdata`,
            which supports loading from `.zip` archives (e.g., in an app
            packaged with Py2Exe).
        """
        builder = gtk.Builder()
        # Read glade file using `pkgutil` to also support loading from `.zip`
        # files (e.g., in app packaged with Py2Exe).
        glade_str = pkgutil.get_data(__name__,
                                     'glade/form_view_dialog.glade')
        builder.add_from_string(glade_str)

        self.window = builder.get_object('form_view_dialog')
        self.vbox_form = builder.get_object('vbox_form')
        if self.title:
            self.window.set_title(self.title)
        if self.short_desc:
            self.short_label = gtk.Label()
            self.short_label.set_text(self.short_desc)
            self.short_label.set_alignment(0, .5)
            self.vbox_form.pack_start(self.short_label, expand=True, fill=True)
        if self.long_desc:
            self.long_label = gtk.Label()
            self.long_label.set_text(self.long_desc)
            self.long_label.set_alignment(.1, .5)
            self.long_expander = gtk.Expander(label='Details')
            self.long_expander.set_spacing(5)
            self.long_expander.add(self.long_label)
            self.vbox_form.pack_start(self.long_expander, expand=True,
                                      fill=True)
        if self.parent is None:
            self.parent = self.default_parent
        self.window.set_default_response(gtk.RESPONSE_OK)
        self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        if self.parent:
            self.window.set_transient_for(self.parent)
        self.window.show_all()

# === BLOCK 4 (label=lm, source_idx=line8866_lm, name=p_scope) ===
def p_scope(p):
    """scope : ',' SCOPE '(' metaElementList ')'"""
    p[0] = p[4]

# === BLOCK 5 (label=lm, source_idx=line4189_lm, name=prep_jid) ===
def prep_jid(nocache=False, passed_jid=None):
    """
    Return a job id and prepare the job id directory
    This is the function responsible for making sure jids don't collide (unless
    its passed a jid)
    So do what you have to do to make sure that stays the case
    """
    if passed_jid:
        jid = passed_jid
    else:
        if nocache:
            jid = str(uuid.uuid4())
        else:
            while True:
                jid = str(uuid.uuid4())
                if not os.path.exists(os.path.join(opts['cachedir'], 'jobs', jid)):
                    break
    return jid

# === BLOCK 6 (label=human, source_idx=line7937_human, name=_validI) ===
def _validI(x, y, weights):
    """
    return indices that have enough data points and are not erroneous 
    """
    # density filter:
    i = np.logical_and(np.isfinite(y), weights > np.median(weights))
    # filter outliers:
    try:
        grad = np.abs(np.gradient(y[i]))
        max_gradient = 4 * np.median(grad)
        i[i][grad > max_gradient] = False
    except (IndexError, ValueError):
        pass
    return i
