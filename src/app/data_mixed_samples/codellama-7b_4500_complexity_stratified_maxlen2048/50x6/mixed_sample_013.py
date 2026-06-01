# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line7025_lm, name=values_for_enum) ===
def values_for_enum(gtype):
    """Get all values for a enum (gtype)."""
    return [v.value for v in gtype]

# === BLOCK 2 (label=human, source_idx=line247_human, name=_reflect_all) ===
def _reflect_all(exclude_tables=None, admin=None, read_only=False, schema=None):
    """Register all tables in the given database as services.

    :param list exclude_tables: A list of tables to exclude from the API
                                service
    """
    AutomapModel.prepare(  # pylint:disable=maybe-no-member
        db.engine, reflect=True, schema=schema)
    for cls in AutomapModel.classes:
        if exclude_tables and cls.__table__.name in exclude_tables:
            continue
        if read_only:
            cls.__methods__ = {'GET'}
        register_model(cls, admin)

# === BLOCK 3 (label=human, source_idx=line8981_human, name=split_func_name_args_params_handle) ===
def split_func_name_args_params_handle(tokens):
    """Process splitting a function into name, params, and args."""
    internal_assert(len(tokens) == 2, "invalid function definition splitting tokens", tokens)
    func_name = tokens[0]
    func_args = []
    func_params = []
    for arg in tokens[1]:
        if len(arg) > 1 and arg[0] in ("*", "**"):
            func_args.append(arg[1])
        elif arg[0] != "*":
            func_args.append(arg[0])
        func_params.append("".join(arg))
    return [
        func_name,
        ", ".join(func_args),
        "(" + ", ".join(func_params) + ")",
    ]

# === BLOCK 4 (label=lm, source_idx=line5422_lm, name=create_ui) ===
def create_ui(self):
        """
        .. versionchanged:: 0.21.2
            Load the builder configuration file using :func:`pkgutil.getdata`,
            which supports loading from `.zip` archives (e.g., in an app
            packaged with Py2Exe).
        """
        # Load the builder configuration file
        builder_config = pkgutil.getdata(__name__, 'builder_config.xml')
        # Create the builder
        builder = UIBuilder(builder_config)
        # Create the UI
        builder.create_ui(self)

# === BLOCK 5 (label=lm, source_idx=line7833_lm, name=cleanup_images) ===
def cleanup_images(self):
        """
        Remove all images created by CONU and remove all hidden images (cached dowloads)

        :return: None
        """
        images = self.client.images.list()
        for image in images:
            if image.tags:
                for tag in image.tags:
                    if tag.startswith("conu"):
                        self.client.images.remove(image.id, force=True)
                        break

        # remove hidden images
        images = self.client.images.list(all=True)
        for image in images:
            if image.attrs["Parent"] == "":
                self.client.images.remove(image.id, force=True)

# === BLOCK 6 (label=human, source_idx=line7258_human, name=hideEvent) ===
def hideEvent(self, event):
        """
        Sets the visible state for this widget.  If it is the first time this
        widget will be visible, the initialized signal will be emitted.

        :param      state | <bool>
        """
        super(XView, self).hideEvent(event)

        # record the visible state for this widget to be separate of Qt's
        # system to know if this view WILL be visible or not once the 
        # system is done processing.  This will affect how signals are
        # validated as part of the visible slot delegation
        self._visibleState = False

        if not self.signalsBlocked():
            self.visibleStateChanged.emit(False)
            QTimer.singleShot(0, self.hidden)
