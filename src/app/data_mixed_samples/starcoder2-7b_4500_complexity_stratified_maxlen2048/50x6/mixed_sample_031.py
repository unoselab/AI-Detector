# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6753_lm, name=clock_resized_cb) ===
def clock_resized_cb(self, viewer, width, height):
        """This method is called when an individual clock is resized.
        It deletes and reconstructs the placement of the text objects
        in the canvas.
        """
        # Delete the old text objects
        for text in self.text_objects:
            viewer.delete_object(text)
        self.text_objects = []

        # Reconstruct the text objects
        for i, clock in enumerate(self.clocks):
            text = viewer.create_text(
                clock.x, clock.y,
                text=clock.text,
                font=self.font,
                fill=self.font_color,
                anchor=self.anchor,
                justify=self.justify,
                angle=clock.angle,
                scale=clock.scale,
                layer=self.layer,
            )
            self.text_objects.append(text)

# === BLOCK 2 (label=human, source_idx=line6322_human, name=_append_seed) ===
def _append_seed(self, seed_type: str, data: Any) -> 'Seeding':
        """Add a seeding method and returns self.

        :returns: self for fluid API
        """
        self.append({
            SEED_METHOD: seed_type,
            SEED_DATA: data,
        })
        return self

# === BLOCK 3 (label=human, source_idx=line6525_human, name=d_from_format) ===
def d_from_format(self, attr):
        """ Find out the local name of an attribute

        :param attr: An Attribute dictionary
        :return: The local attribute name or "" if no mapping could be made
        """
        if attr["name_format"]:
            if self.name_format == attr["name_format"]:
                try:
                    return self._fro[attr["name"].lower()]
                except KeyError:
                    pass
        else:  # don't know the name format so try all I have
            try:
                return self._fro[attr["name"].lower()]
            except KeyError:
                pass

        return ""

# === BLOCK 4 (label=human, source_idx=line1318_human, name=revert) ===
def revert(self, unchanged=False):
        """Reverts any file changes

        :param unchanged: Only revert if the file is unchanged
        :type unchanged: bool
        """
        cmd = ['revert']
        if unchanged:
            cmd.append('-a')

        wasadd = self.action == 'add'

        cmd.append(self.depotFile)

        self._connection.run(cmd)

        if 'movedFile' in self._p4dict:
            self._p4dict['depotFile'] = self._p4dict['movedFile']

        if not wasadd:
            self.query()

        if self._changelist:
            self._changelist.remove(self, permanent=True)

# === BLOCK 5 (label=lm, source_idx=line1835_lm, name=K) ===
def K(self,X,X2,target):
        """Compute the covariance matrix between X and X2."""
        return self.kernel(X,X2,target)

# === BLOCK 6 (label=lm, source_idx=line4903_lm, name=handle_aliases_in_init_files) ===
def handle_aliases_in_init_files(name, import_alias_mapping):
    """Returns either None or the handled alias.
    Used in add_module.
    """
    if name in import_alias_mapping:
        return import_alias_mapping[name]
    return None
