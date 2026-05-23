# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1919_lm, name=cmd_command_int) ===
def cmd_command_int(self, args):
        """execute supplied command_int"""
        self.command_int(args)

# === BLOCK 2 (label=human, source_idx=line1471_human, name=add_fields) ===
def add_fields(self, fields):
        """Add the fields to their corresponding container.

        `fields` is an iterable of field objects from osrframework.thirdparties.pipl_com.lib.fields.

        """
        for field in fields:
            cls = field.__class__
            try:
                container = FieldsContainer.class_container[cls]
            except KeyError:
                raise ValueError('Object of type %s is an invalid field' % cls)
            getattr(self, container).append(field)

# === BLOCK 3 (label=human, source_idx=line274_human, name=add_dependency) ===
def add_dependency(self, from_task_name, to_task_name):
        """ Add a dependency between two tasks. """

        logger.debug('Adding dependency from {0} to {1}'.format(from_task_name, to_task_name))
        if not self.state.allow_change_graph:
            raise DagobahError("job's graph is immutable in its current state: %s"
                               % self.state.status)

        self.add_edge(from_task_name, to_task_name)
        self.commit()

# === BLOCK 4 (label=lm, source_idx=line2718_lm, name=start_dag) ===
def start_dag(self, dag, *, data=None):
        """ Schedule the execution of a dag by sending a signal to the workflow.

        Args:
            dag (Dag, str): The dag object or the name of the dag that should be started.
            data (MultiTaskData): The data that should be passed on to the new dag.

        Returns:
            str: The name of the successfully started dag.
        """
        if isinstance(dag, Dag):
            dag_name = dag.name
        else:
            dag_name = dag
        self.workflow.send_signal(dag_name, data=data)
        return dag_name

# === BLOCK 5 (label=lm, source_idx=line1709_lm, name=rsem_stats_table) ===
def rsem_stats_table(self):
        """ Take the parsed stats from the rsem report and add them to the
        basic stats table at the top of the report """
        stats_table = []
        for stat in self.stats:
            stats_table.append([stat['name'], stat['value']])
        return stats_table

# === BLOCK 6 (label=human, source_idx=line1909_human, name=get) ===
def get(key, default=-1):
        """Backport support for original codes."""
        if isinstance(key, int):
            return RouterAlert(key)
        if key not in RouterAlert._member_map_:
            extend_enum(RouterAlert, key, default)
        return RouterAlert[key]
