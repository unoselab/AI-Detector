# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line721_human, name=to_string) ===
def to_string(self, buf=None, format_abs_ref_as='string',
                  upper_triangle=True, header=True, index=True, **kwargs):
        """Render a DataFrame to a console-friendly tabular output.

        Wrapper around the :meth:`pandas.DataFrame.to_string` method.
        """
        out = self._sympy_formatter()
        out = out._abs_ref_formatter(format_as=format_abs_ref_as)
        if not upper_triangle:
            out = out._remove_upper_triangle()

        content = out._frame.to_string(buf=buf, header=header, index=index,
                                       **kwargs)
        if not index and not header:
            # NOTE(the following might be removed in the future
            # introduced because of formatting bug in pandas
            # See https://github.com/pandas-dev/pandas/issues/13032)
            space = ' ' * (out.loc[:, 'atom'].str.len().max()
                           - len(out.iloc[0, 0]))
            content = space + content
        return content

# === BLOCK 2 (label=lm, source_idx=line1338_lm, name=close) ===
def close(self, code=None):
        """return a `close` :class:`Frame`.
        """
        return self.frame(code=code)

# === BLOCK 3 (label=lm, source_idx=line1052_lm, name=get) ===
def get(self, name, failobj=None):
        """Get a header value.

        Like __getitem__() but return failobj instead of None when the field
        is missing.
        """
        try:
            return self[name]
        except KeyError:
            return failobj

# === BLOCK 4 (label=lm, source_idx=line4351_lm, name=license_install) ===
def license_install(self, license_file):
        """
        Install a new license.

        :param str license_file: fully qualified path to the
            license jar file.
        :raises: ActionCommandFailed
        :return: None
        """
        self.logger.info("Installing license file: %s", license_file)
        cmd = ["installLicense", "-license", license_file]
        self.run_action_command(cmd)

# === BLOCK 5 (label=human, source_idx=line3686_human, name=DrawIconAndLabel) ===
def DrawIconAndLabel(self, dc, node, x, y, w, h, depth):
        """ Draw the icon, if any, and the label, if any, of the node. """
        if w-2 < self._em_size_//2 or h-2 < self._em_size_ //2:
            return
        dc.SetClippingRegion(x+1, y+1, w-2, h-2) # Don't draw outside the box
        try:
            icon = self.adapter.icon(node, node==self.selectedNode)
            if icon and h >= icon.GetHeight() and w >= icon.GetWidth():
                iconWidth = icon.GetWidth() + 2
                dc.DrawIcon(icon, x+2, y+2)
            else:
                iconWidth = 0
            if self.labels and h >= dc.GetTextExtent('ABC')[1]:
                dc.SetTextForeground(self.TextForegroundForNode(node, depth))
                dc.DrawText(self.adapter.label(node), x + iconWidth + 2, y+2)
        finally:
            dc.DestroyClippingRegion()

# === BLOCK 6 (label=human, source_idx=line5090_human, name=generics) ===
def generics(self):
        """Iterates over the defined Generics."""
        defgeneric = lib.EnvGetNextDefgeneric(self._env, ffi.NULL)

        while defgeneric != ffi.NULL:
            yield Generic(self._env, defgeneric)

            defgeneric = lib.EnvGetNextDefgeneric(self._env, defgeneric)
