# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1311_lm, name=fit) ===
def fit(self, train_X, train_Y, val_X=None, val_Y=None, graph=None):
        """Fit the model to the data.

        Parameters
        ----------

        train_X : array_like, shape (n_samples, n_features)
            Training data.

        train_Y : array_like, shape (n_samples, n_classes)
            Training labels.

        val_X : array_like, shape (N, n_features) optional, (default = None).
            Validation data.

        val_Y : array_like, shape (N, n_classes) optional, (default = None).
            Validation labels.

        graph : tf.Graph, optional (default = None)
            Tensorflow Graph object.

        Returns
        -------
        """

# === BLOCK 2 (label=human, source_idx=line3097_human, name=DFS) ===
def DFS(G):
    """
    Algorithm for depth-first searching the vertices of a graph.
    """
    if not G.vertices:
        raise GraphInsertError("This graph have no vertices.")
    color = {}
    pred = {}
    reach = {}
    finish = {}

    def DFSvisit(G, current, time):
        color[current] = 'grey'
        time += 1
        reach[current] = time
        for vertex in G.vertices[current]:
            if color[vertex] == 'white':
                pred[vertex] = current
                time = DFSvisit(G, vertex, time)
        color[current] = 'black'
        time += 1
        finish[current] = time
        return time

    for vertex in G.vertices:
        color[vertex] = 'white'
        pred[vertex] = None
        reach[vertex] = 0
        finish[vertex] = 0
    time = 0
    for vertex in G.vertices:
        if color[vertex] == 'white':
            time = DFSvisit(G, vertex, time)
    # Dictionary for vertex data after DFS
    # -> vertex_data = {vertex: (predecessor, reach, finish), }
    vertex_data = {}
    for vertex in G.vertices:
        vertex_data[vertex] = (pred[vertex], reach[vertex], finish[vertex])
    return vertex_data

# === BLOCK 3 (label=lm, source_idx=line1525_lm, name=sortLocations) ===
def sortLocations(locations):
    """ Sort the locations by ranking:
            1.  all on-axis points
            2.  all off-axis points which project onto on-axis points
                these would be involved in master to master interpolations
                necessary for patching. Projecting off-axis masters have
                at least one coordinate in common with an on-axis master.
            3.  non-projecting off-axis points, 'wild' off axis points
                These would be involved in projecting limits and need to be patched.
    """

# === BLOCK 4 (label=human, source_idx=line4425_human, name=count) ===
def count(self, axis='major'):
        """
        Return number of observations over requested axis.

        Parameters
        ----------
        axis : {'items', 'major', 'minor'} or {0, 1, 2}

        Returns
        -------
        count : DataFrame
        """
        i = self._get_axis_number(axis)

        values = self.values
        mask = np.isfinite(values)
        result = mask.sum(axis=i, dtype='int64')

        return self._wrap_result(result, axis)

# === BLOCK 5 (label=lm, source_idx=line2886_lm, name=_skip_whitespace) ===
def _skip_whitespace(self):
        """Increment over whitespace, counting characters."""
        count = 0
        txt = getattr(self, "text", "")
        pos = getattr(self, "pos", 0)
        line = getattr(self, "line", 1)
        col = getattr(self, "column", 1)
        length = len(txt)

        while pos < length and txt[pos].isspace():
            ch = txt[pos]
            pos += 1
            count += 1
            if ch == "\n":
                line += 1
                col = 1
            else:
                col += 1

        self.pos = pos
        if hasattr(self, "line"):
            self.line = line
        if hasattr(self, "column"):
            self.column = col
        return count

# === BLOCK 6 (label=human, source_idx=line3385_human, name=get_version) ===
def get_version(extension, workflow_file):
    """Determines the version of a .py, .wdl, or .cwl file."""
    if extension == 'py' and two_seven_compatible(workflow_file):
        return '2.7'
    elif extension == 'cwl':
        return yaml.load(open(workflow_file))['cwlVersion']
    else:  # Must be a wdl file.
        # Borrowed from https://github.com/Sage-Bionetworks/synapse-orchestrator/blob/develop/synorchestrator/util.py#L142
        try:
            return [l.lstrip('version') for l in workflow_file.splitlines() if 'version' in l.split(' ')][0]
        except IndexError:
            return 'draft-2'
