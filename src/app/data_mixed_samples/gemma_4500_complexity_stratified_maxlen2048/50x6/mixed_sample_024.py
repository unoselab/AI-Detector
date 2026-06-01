# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line7995_lm, name=_find_new_additions) ===
def _find_new_additions(self):
        """Find any nodes in the graph that need to be added to the internal
        queue and add them.

        Callers must hold the lock.
        """
        for node in self._graph.nodes:
            if node not in self._queue and node not in self._visited:
                self._queue.append(node)

# === BLOCK 2 (label=human, source_idx=line8789_human, name=arcball_map_to_sphere) ===
def arcball_map_to_sphere(point, center, radius):
    """Return unit sphere coordinates from window coordinates."""
    v0 = (point[0] - center[0]) / radius
    v1 = (center[1] - point[1]) / radius
    n = v0*v0 + v1*v1
    if n > 1.0:
        # position outside of sphere
        n = math.sqrt(n)
        return numpy.array([v0/n, v1/n, 0.0])
    else:
        return numpy.array([v0, v1, math.sqrt(1.0 - n)])

# === BLOCK 3 (label=human, source_idx=line1605_human, name=extend_schema_spec) ===
def extend_schema_spec(self) -> None:
        """ Injects the block start and end times """
        super().extend_schema_spec()

        if self.ATTRIBUTE_FIELDS in self._spec:
            # Add new fields to the schema spec. Since `_identity` is added by the super, new elements are added after
            predefined_field = self._build_time_fields_spec(self._spec[self.ATTRIBUTE_NAME])
            self._spec[self.ATTRIBUTE_FIELDS][1:1] = predefined_field

            # Add new field schema to the schema loader
            for field_schema in predefined_field:
                self.schema_loader.add_schema_spec(field_schema, self.fully_qualified_name)

# === BLOCK 4 (label=lm, source_idx=line8250_lm, name=seek) ===
def seek(self, time):
        """Attempts to seek in the stream.

        :param time: int, Time to seek to in seconds

        """
        self.stream.seek(time)

# === BLOCK 5 (label=lm, source_idx=line7917_lm, name=smart) ===
def smart(**kwargs):
    """
    Simple decorator to get custom fields on admin class, using this you will use less line codes

    :param short_description: description of custom field
    :type str:

    :param admin_order_field: field to order on click
    :type str:

    :param allow_tags: allow html tags
    :type bool:

    :param boolean: if field is True, False or None
    :type bool:

    :param empty_value_display: Default value when field is null
    :type str:

    :return: method decorated
    :rtype: method
    """
    for key, value in kwargs.items():
        setattr(func, key, value)
    return func
return decorator

# === BLOCK 6 (label=human, source_idx=line5942_human, name=fill_clipboard) ===
def fill_clipboard(self, contents):
        """
        Copy text into the clipboard

        Usage: C{clipboard.fill_clipboard(contents)}

        @param contents: string to be placed in the selection
        """
        Gdk.threads_enter()
        if Gtk.get_major_version() >= 3:
            self.clipBoard.set_text(contents, -1)
        else:
            self.clipBoard.set_text(contents)
        Gdk.threads_leave()
