# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1031_human, name=keep_color) ===
def keep_color(ax=None):
    """ Keep the same color for the same graph. 
    Warning: due to the structure of Python iterators I couldn't help but
    iterate over all the cycle twice. One first time to get the number of elements
    in the cycle, one second time to stop just before the last. And this still 
    only works assuming your cycle doesn't contain the object twice

    Note: when setting color= it looks like the color cycle state is not called

    TODO: maybe implement my own cycle structure """

    if ax is None:
        ax = mpl.pyplot.gca()

    i = 1  # count number of elements
    cycle = ax._get_lines.prop_cycler
    a = next(cycle)     # a is already the next one.
    while(a != next(cycle)):
        i += 1
    # We want a-1 to show up on next call to next. So a-2 must be set now
    for j in range(i - 2):
        next(cycle)

# === BLOCK 2 (label=lm, source_idx=line705_lm, name=last_ehlo_response) ===
def last_ehlo_response(self, response: SMTPResponse) -> None:
        """
        When setting the last EHLO response, parse the message for supported
        extensions and auth methods.
        """
        self.ehlo_response = response
        self.supported_extensions = {}
        self.auth_methods = []
        for line in response.splitlines():
            if line.startswith("AUTH"):
                self.auth_methods = line.split()[1:]
            else:
                self.supported_extensions[line.split()[0]] = line

# === BLOCK 3 (label=lm, source_idx=line1550_lm, name=_should_get_another_batch) ===
def _should_get_another_batch(self, content):
    """Whether to issue another GET bucket call.

    Args:
      content: response XML.

    Returns:
      True if should, also update self._options for the next request.
      False otherwise.
    """
    if not content:
        return False
    next_continuation_token = content.find('NextContinuationToken').text
    if not next_continuation_token:
        return False
    self._options['continuation_token'] = next_continuation_token
    return True

# === BLOCK 4 (label=lm, source_idx=line488_lm, name=data) ===
def data(self, index, role=Qt.DisplayRole):
        """Override Qt method"""
        if role == Qt.DisplayRole:
            return str(self.data_dict[index.row()])
        else:
            return None

# === BLOCK 5 (label=human, source_idx=line2234_human, name=register_view) ===
def register_view(self, view):
        """Called when the View was registered

        Can be used e.g. to connect signals. Here, the destroy signal is connected to close the application
        """
        super(StateOutcomesListController, self).register_view(view)
        if isinstance(view, StateOutcomesTreeView):
            self.connect_signal(view['to_state_combo'], "edited", self.on_to_state_edited)
            self.connect_signal(view['to_outcome_combo'], "edited", self.on_to_outcome_edited)

        if isinstance(self.model.state, LibraryState) or self.model.state.get_next_upper_library_root_state():
            view['id_cell'].set_property('editable', False)
            view['name_cell'].set_property('editable', False)

        self._apply_value_on_edited_and_focus_out(view['name_cell'], self.apply_new_outcome_name)

        self.update(initiator='"register view"')

# === BLOCK 6 (label=human, source_idx=line4558_human, name=getedges) ===
def getedges(fname, iddfile):
    """return the edges of the idf file fname"""
    data, commdct, _idd_index = readidf.readdatacommdct(fname, iddfile=iddfile)
    edges = makeairplantloop(data, commdct)
    return edges
