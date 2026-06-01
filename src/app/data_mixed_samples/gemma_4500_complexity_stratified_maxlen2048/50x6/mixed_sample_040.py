# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3213_lm, name=__get_file) ===
def __get_file(self, file):
        """ Get request file and do a security check """
        if not file:
            return None

        filename = file.filename
        if not filename:
            raise ValueError("File has no filename")

        # Basic security check: prevent directory traversal
        import os
        base_name = os.path.basename(filename)
        if base_name != filename:
            raise PermissionError("Invalid filename detected")

        return file

# === BLOCK 2 (label=human, source_idx=line5907_human, name=_new_empty_handle) ===
def _new_empty_handle():
    """Returns a new empty handle.

    Empty handle can be used to hold a result.

    Returns
    -------
    handle
        A new empty `NDArray` handle.
    """
    hdl = NDArrayHandle()
    check_call(_LIB.MXNDArrayCreateNone(ctypes.byref(hdl)))
    return hdl

# === BLOCK 3 (label=human, source_idx=line5426_human, name=reload_dependencies) ===
def reload_dependencies(force=False):
    """
    Reloads all python modules that law depends on. Currently, this is just *luigi* and *six*.
    Unless *force* is *True*, multiple calls to this function will not have any effect.
    """
    global _reloaded_deps

    if _reloaded_deps and not force:
        return
    _reloaded_deps = True

    for mod in deps:
        six.moves.reload_module(mod)
        logger.debug("reloaded module '{}'".format(mod))

# === BLOCK 4 (label=lm, source_idx=line8724_lm, name=_operator_handling) ===
def _operator_handling(self, cursor):
        """Returns a string with the literal that are part of the operation."""
        result = ""
        while cursor.current_token_type in ('OPERATOR', 'LITERAL', 'WHITESPACE'):
            result += cursor.current_token_value
            cursor.advance()
        return result

# === BLOCK 5 (label=lm, source_idx=line4215_lm, name=render) ===
def render(self, name, value, attrs=None):
        """
        Render the ``icekit_events/recurrence_rule_widget/render.html``
        template with the following context:

            rendered_widgets
                The rendered widgets.
            id
                The ``id`` attribute from the ``attrs`` keyword argument.
            recurrence_rules
                A JSON object mapping recurrence rules to their primary keys.

        The default template adds JavaScript event handlers that update the
        ``Textarea`` and ``Select`` widgets when they are updated.
        """
        attrs = attrs or {}
        context = {
            'rendered_widgets': rendered_widgets,
            'id': attrs.get('id'),
            'recurrence_rules': self.recurrence_rules_json,
        }
        return self.render_template('icekit_events/recurrence_rule_widget/render.html', context)

# === BLOCK 6 (label=human, source_idx=line7846_human, name=add_file_ident_desc) ===
def add_file_ident_desc(self, new_fi_desc, logical_block_size):
        # type: (UDFFileIdentifierDescriptor, int) -> int
        """
        A method to add a new UDF File Identifier Descriptor to this UDF File
        Entry.

        Parameters:
         new_fi_desc - The new UDF File Identifier Descriptor to add.
         logical_block_size - The logical block size to use.
        Returns:
         The number of extents added due to adding this File Identifier Descriptor.
        """
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError('UDF File Entry not initialized')

        if self.icb_tag.file_type != 4:
            raise pycdlibexception.PyCdlibInvalidInput('Can only add a UDF File Identifier to a directory')

        self.fi_descs.append(new_fi_desc)

        num_bytes_to_add = UDFFileIdentifierDescriptor.length(len(new_fi_desc.fi))

        old_num_extents = 0
        # If info_len is 0, then this is a brand-new File Entry, and thus the
        # number of extents it is using is 0.
        if self.info_len > 0:
            old_num_extents = utils.ceiling_div(self.info_len, logical_block_size)

        self.info_len += num_bytes_to_add
        new_num_extents = utils.ceiling_div(self.info_len, logical_block_size)

        self.log_block_recorded = new_num_extents

        self.alloc_descs[0][0] = self.info_len
        if new_fi_desc.is_dir():
            self.file_link_count += 1

        return new_num_extents - old_num_extents
