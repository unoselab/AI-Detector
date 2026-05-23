# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line355_lm, name=set_context) ===
def set_context(self, cell_type):
        """Set protein expression data and mutational status as node attribute

        This method uses :py:mod:`indra.databases.context_client` to get
        protein expression levels and mutational status for a given cell type
        and set a node attribute for proteins accordingly.

        Parameters
        ----------
        cell_type : str
            Cell type name for which expression levels are queried.
            The cell type name follows the CCLE database conventions.
            Example: LOXIMVI_SKIN, BT20_BREAST
        """
        for node in self.nodes:
            if node.type == 'protein':
                node.expression = context_client.get_expression(node.name, cell_type)
                node.mutation = context_client.get_mutation(node.name, cell_type)

# === BLOCK 2 (label=human, source_idx=line1577_human, name=generate_csv) ===
def generate_csv(src, out):
    """\
    Walks through `src` and generates the CSV file `out`
    """
    writer = UnicodeWriter(open(out, 'wb'), delimiter=';')
    writer.writerow(('Reference ID', 'Created', 'Origin', 'Subject'))
    for cable in cables_from_source(src, predicate=pred.origin_filter(pred.origin_germany)):
        writer.writerow((cable.reference_id, cable.created, cable.origin, titlefy(cable.subject)))

# === BLOCK 3 (label=lm, source_idx=line1958_lm, name=get_or_create_environment) ===
def get_or_create_environment(self, id=None, name=None, zone=None, default=False):
        """ Get environment by id or name.
        If not found: create with given or generated parameters
        """
        if id:
            environment = self.get_environment(id)
        elif name:
            environment = self.get_environment_by_name(name)
        else:
            environment = self.create_environment(name, zone, default)

        return environment

# === BLOCK 4 (label=human, source_idx=line2264_human, name=_visible_width) ===
def _visible_width(s):
    """Visible width of a printed string. ANSI color codes are removed.

    >>> _visible_width('\x1b[31mhello\x1b[0m'), _visible_width("world")
    (5, 5)

    """
    if isinstance(s, _text_type) or isinstance(s, _binary_type):
        return _max_line_width(_strip_invisible(s))
    else:
        return _max_line_width(_text_type(s))

# === BLOCK 5 (label=human, source_idx=line1958_human, name=get_or_create_environment) ===
def get_or_create_environment(self, id=None, name=None, zone=None, default=False):
        """ Get environment by id or name.
        If not found: create with given or generated parameters
        """
        if id:
            return self.get_environment(id=id)
        elif name:
            try:
                env = self.get_environment(name=name)
                self._assert_env_and_zone(env, zone)
            except exceptions.NotFoundError:
                env = self.create_environment(name=name, zone=zone, default=default)
            return env
        else:
            name = 'auto-generated-env'
            return self.create_environment(name=name, zone=zone, default=default)

# === BLOCK 6 (label=lm, source_idx=line274_lm, name=add_dependency) ===
def add_dependency(self, from_task_name, to_task_name):
        """ Add a dependency between two tasks. """
        if from_task_name not in self.tasks:
            raise ValueError(f"Task '{from_task_name}' not found.")
        if to_task_name not in self.tasks:
            raise ValueError(f"Task '{to_task_name}' not found.")
        self.tasks[from_task_name].add_dependency(to_task_name)
