# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3738_human, name=same) ===
def same(d1, d2):
    """! @brief Test whether two sequences contain the same values.

    Unlike a simple equality comparison, this function works as expected when the two sequences
    are of different types, such as a list and bytearray. The sequences must return
    compatible types from indexing.
    """
    if len(d1) != len(d2):
        return False
    for i in range(len(d1)):
        if d1[i] != d2[i]:
            return False
    return True

# === BLOCK 2 (label=lm, source_idx=line5589_lm, name=from_dict) ===
def from_dict(d):
    """
    load an nparray object from a dictionary

    @parameter str d: dictionary representing the nparray object
    """
    return np.array(d['data'], dtype=d['dtype'])

# === BLOCK 3 (label=lm, source_idx=line3388_lm, name=post) ===
def post(self, path, data):
        """
        Generic POST with headers
        """
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        return self.session.post(self.url + path, data=json.dumps(data), headers=headers)

# === BLOCK 4 (label=human, source_idx=line7285_human, name=get_service_reference) ===
def get_service_reference(self, clazz, ldap_filter=None):
        # type: (Optional[str], Optional[str]) -> Optional[ServiceReference]
        """
        Returns a ServiceReference object for a service that implements and
        was registered under the specified class

        :param clazz: The class name with which the service was registered.
        :param ldap_filter: A filter on service properties
        :return: A service reference, None if not found
        """
        result = self.__framework.find_service_references(
            clazz, ldap_filter, True
        )
        try:
            return result[0]
        except TypeError:
            return None

# === BLOCK 5 (label=human, source_idx=line6454_human, name=start) ===
def start(self, nodes=None):
        """Start one or many nodes.

        :param   nodes: Nodes to be started.
        :type    nodes: ``list``
        """
        if not self.is_connected():
            return None

        nodes = nodes or self.nodes
        result = []

        for node in nodes:
            if node.state == 'running':
                logging.warning('Node %s is already "running".', node.name)
                continue
            try:
                status = self.gce.ex_start_node(node)
                if status:
                    result.append(node)
            except InvalidRequestError as err:
                raise ComputeEngineManagerException(err)

        return result

# === BLOCK 6 (label=lm, source_idx=line6658_lm, name=parse_ast) ===
def parse_ast(source, filename=None):
    """Parse source into a Python AST, taking care of encoding."""
    if filename:
        source = ustr(source, encoding=FS_ENCODING)
    else:
        source = ustr(source)
    try:
        return ast.parse(source, filename=filename)
    except SyntaxError:
        # Workaround for https://bugs.python.org/issue19308
        source = source.encode('utf8')
        return ast.parse(source, filename=filename)
