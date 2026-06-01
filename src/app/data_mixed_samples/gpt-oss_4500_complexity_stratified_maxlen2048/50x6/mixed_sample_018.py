# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line855_lm, name=expand_expression) ===
def expand_expression(self, pattern, hosts, services, hostgroups, servicegroups, running=False):
        # pylint: disable=too-many-locals
        """Expand a host or service expression into a dependency node tree
        using (host|service)group membership, regex, or labels as item selector.

        :param pattern: pattern to parse
        :type pattern: str
        :param hosts: hosts list, used to find a specific host
        :type hosts: alignak.objects.host.Host
        :param services: services list, used to find a specific service
        :type services: alignak.objects.service.Service
        :param running: rules are evaluated at run time and parsing. True means runtime
        :type running: bool
        :return: root node of parsed tree
        :rtype: alignak.dependencynode.DependencyNode
        """

# === BLOCK 2 (label=human, source_idx=line1711_human, name=launch_server) ===
def launch_server(message_handler, options):
    """
    Launch a message server
    :param handler_function: The handler function to execute for each message
    :param options: Application options for TCP, etc.
    """
    logger = logging.getLogger(__name__)
    if (options.debug):
        logger.setLevel(logging.DEBUG)

    if not options.monitor_port:
        logger.warning(
            "Monitoring not enabled. No monitor-port option defined.")
    else:
        threading.Thread(target=launch_monitor_server, args=(options.host, options.monitor_port, logger)).start()

    # Create the server, binding to specified host on configured port

    logger.info(
        'Starting server on host %s port %d Python version %s.%s.%s' % ((options.host, options.port) + sys.version_info[:3]))
    server = ThreadedTCPServer((options.host, options.port),
                       StreamHandler.create_handler(message_handler,
                                                    options.buffer_size,
                                                    logger))

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Ctrl-C, exiting...")
        os._exit(142)

# === BLOCK 3 (label=human, source_idx=line4916_human, name=find_unconserved_metabolites) ===
def find_unconserved_metabolites(model):
    """
    Detect unconserved metabolites.

    Parameters
    ----------
    model : cobra.Model
        The metabolic model under investigation.

    Notes
    -----
    See [1]_ section 3.2 for a complete description of the algorithm.


    .. [1] Gevorgyan, A., M. G Poolman, and D. A Fell.
           "Detection of Stoichiometric Inconsistencies in Biomolecular
           Models."
           Bioinformatics 24, no. 19 (2008): 2245.

    """
    problem = model.problem
    stoich_trans = problem.Model()
    internal_rxns = con_helpers.get_internals(model)
    metabolites = set(met for rxn in internal_rxns for met in rxn.metabolites)
    # The binary variables k[i] in the paper.
    k_vars = list()
    for met in metabolites:
        # The element m[i] of the mass vector.
        m_var = problem.Variable(met.id)
        k_var = problem.Variable("k_{}".format(met.id), type="binary")
        k_vars.append(k_var)
        stoich_trans.add([m_var, k_var])
        # This constraint is equivalent to 0 <= k[i] <= m[i].
        stoich_trans.add(problem.Constraint(
            k_var - m_var, ub=0, name="switch_{}".format(met.id)))
    stoich_trans.update()
    con_helpers.add_reaction_constraints(
        stoich_trans, internal_rxns, problem.Constraint)
    # The objective is to maximize the binary indicators k[i], subject to the
    # above inequality constraints.
    stoich_trans.objective = problem.Objective(
        Zero, sloppy=True, direction="max")
    stoich_trans.objective.set_linear_coefficients(
        {var: 1. for var in k_vars})
    status = stoich_trans.optimize()
    if status == OPTIMAL:
        # TODO: See if that could be a Boolean test `bool(var.primal)`.
        return set([model.metabolites.get_by_id(var.name[2:])
                    for var in k_vars if var.primal < 0.8])
    else:
        raise RuntimeError(
            "Could not compute list of unconserved metabolites."
            " Solver status is '{}' (only optimal expected).".format(status))

# === BLOCK 4 (label=lm, source_idx=line160_lm, name=_load_models) ===
def _load_models(self) -> None:
        """Maybe load all the models to be assembled together and save them to the ``self._models`` attribute."""
        if getattr(self, "_models", None):
            return
        models = {}
        specs = getattr(self, "_model_specs", {})
        for name, spec in specs.items():
            if isinstance(spec, str):
                try:
                    import torch
                    model = torch.load(spec, map_location="cpu")
                except Exception:
                    import pickle
                    with open(spec, "rb") as f:
                        model = pickle.load(f)
            elif callable(spec):
                model = spec()
            else:
                model = spec
            models[name] = model
        self._models = models

# === BLOCK 5 (label=lm, source_idx=line532_lm, name=namedb_genesis_block_history_hash) ===
def namedb_genesis_block_history_hash(genesis_block_history):
    """
    Make a "fake" txid for the genesis block history
    Returns a 32-byte hash (single sha256), hex-encoded
    (single sha256 so it can be easily verified against our genesis block tooling)
    """
    import hashlib, json
    if isinstance(genesis_block_history, (bytes, bytearray)):
        data = bytes(genesis_block_history)
    else:
        # Use deterministic JSON serialization
        data = json.dumps(genesis_block_history, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(data).hexdigest()

# === BLOCK 6 (label=human, source_idx=line6917_human, name=_add_offsets_to_token_nodes) ===
def _add_offsets_to_token_nodes(self):
        """
        Adds primary text string onsets/offsets to all nodes that represent
        tokens. In SaltDocuments, this data was stored in TextualRelation
        edges only.
        """
        for edge_index in self._textual_relation_ids:
            token_node_index = self.edges[edge_index].source
            self.nodes[token_node_index].onset = self.edges[edge_index].onset
            self.nodes[token_node_index].offset = self.edges[edge_index].offset
