# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line6327_human, name=tseitin) ===
def tseitin(self, auxvarname='aux'):
        """Convert the expression to Tseitin's encoding."""
        if self.is_cnf():
            return self

        _, constraints = _tseitin(self.to_nnf(), auxvarname)
        fst = constraints[-1][1]
        rst = [Equal(v, ex).to_cnf() for v, ex in constraints[:-1]]
        return And(fst, *rst)

# === BLOCK 2 (label=lm, source_idx=line1144_lm, name=do_notification_update) ===
def do_notification_update(mc, args):
    """Update notification."""
    # Ensure required identifier is present
    if 'id' not in args:
        raise ValueError("Missing required 'id' in args")
    notif_id = args['id']

    # Build the cache key (adjust prefix as needed for your environment)
    key = f'notification:{notif_id}'

    # Retrieve the existing notification
    existing = mc.get(key)
    if existing is None:
        raise KeyError(f'Notification with id {notif_id} not found')

    # If the stored value is a serialized string (e.g., JSON), attempt to decode it
    if isinstance(existing, (bytes, bytearray)):
        try:
            import json
            existing = json.loads(existing.decode('utf-8'))
        except Exception:
            # Fallback: keep raw bytes if decoding fails
            pass

    # Update the notification with provided fields (excluding the id itself)
    updated = {**existing, **{k: v for k, v in args.items() if k != 'id'}}

    # Serialize back to JSON if the original was JSON‑serializable
    try:
        import json
        payload = json.dumps(updated).encode('utf-8')
    except Exception:
        payload = updated  # store as‑is if it cannot be JSON‑encoded

    # Persist the updated notification
    mc

# === BLOCK 3 (label=lm, source_idx=line2298_lm, name=monitored_resource_descriptor_path) ===
def monitored_resource_descriptor_path(cls, project, monitored_resource_descriptor):
        """Return a fully-qualified monitored_resource_descriptor string."""
        return f"projects/{project}/monitoredResourceDescriptors/{monitored_resource_descriptor}"

# === BLOCK 4 (label=human, source_idx=line6195_human, name=find_feasible_flow) ===
def find_feasible_flow(self):
        """
        API:
            find_feasible_flow(self)
        Description:
            Solves feasible flow problem, stores solution in 'flow' attribute
            or arcs. This method is used to get an initial feasible flow for
            simplex and cycle canceling algorithms. Uses max_flow() method.
            Other max flow methods can also be used. Returns True if a feasible
            flow is found, returns False, if the problem is infeasible. When
            the problem is infeasible 'flow' attributes of arcs should be
            considered as junk.
        Pre:
            (1) 'capacity' attribute of arcs
            (2) 'demand' attribute of nodes
        Post:
            Keeps solution in 'flow' attribute of arcs.
        Return:
            Returns True if a feasible flow is found, returns False, if the
            problem is infeasible
        """
        # establish a feasible flow in the network, to do this add nodes s and
        # t and solve a max flow problem.
        nl = self.get_node_list()
        for i in nl:
            b_i = self.get_node(i).get_attr('demand')
            if b_i > 0:
                # i is a supply node, add (s,i) arc
                self.add_edge('s', i, capacity=b_i)
            elif b_i < 0:
                # i is a demand node, add (i,t) arc
                self.add_edge(i, 't', capacity=-1*b_i)
        # solve max flow on this modified graph
        self.max_flow('s', 't', 'off')
        # check if all demand is satisfied, i.e. the min cost problem is
        # feasible or not
        for i in self.neighbors['s']:
            flow = self.get_edge_attr('s', i, 'flow')
            capacity = self.get_edge_attr('s', i, 'capacity')
            if flow != capacity:
                self.del_node('s')
                self.del_node('t')
                return False
        # remove node 's' and node 't'
        self.del_node('s')
        self.del_node('t')
        return True

# === BLOCK 5 (label=human, source_idx=line5080_human, name=assertFileSizeNotEqual) ===
def assertFileSizeNotEqual(self, filename, size, msg=None):
        """Fail if ``filename`` has the given ``size`` as determined
        by the '!=' operator.

        Parameters
        ----------
        filename : str, bytes, file-like
        size : int, float
        msg : str
            If not provided, the :mod:`marbles.mixins` or
            :mod:`unittest` standard message will be used.

        Raises
        ------
        TypeError
            If ``filename`` is not a str or bytes object and is not
            file-like.
        """
        fsize = self._get_file_size(filename)
        self.assertNotEqual(fsize, size, msg=msg)

# === BLOCK 6 (label=lm, source_idx=line1840_lm, name=attr_set) ===
def attr_set(args):
    """ Set key=value attributes: if entity name & type are specified then
    attributes will be set upon that entity, otherwise the attribute will
    be set at the workspace level"""
