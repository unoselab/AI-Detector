# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3292_human, name=iter_child_nodes) ===
def iter_child_nodes(node, omit=None, _fields_order=_FieldsOrder()):
    """
    Yield all direct child nodes of *node*, that is, all fields that
    are nodes and all items of fields that are lists of nodes.

    :param node:          AST node to be iterated upon
    :param omit:          String or tuple of strings denoting the
                          attributes of the node to be omitted from
                          further parsing
    :param _fields_order: Order of AST node fields
    """
    for name in _fields_order[node.__class__]:
        if omit and name in omit:
            continue
        field = getattr(node, name, None)
        if isinstance(field, ast.AST):
            yield field
        elif isinstance(field, list):
            for item in field:
                yield item

# === BLOCK 2 (label=human, source_idx=line3119_human, name=build_groups) ===
def build_groups(self, tokens):
        """Build dict of groups from list of tokens"""
        groups = {}
        for token in tokens:
            match_type = MatchType.start if token.group_end else MatchType.single
            groups[token.group_start] = (token, match_type)
            if token.group_end:
                groups[token.group_end] = (token, MatchType.end)
        return groups

# === BLOCK 3 (label=lm, source_idx=line3891_lm, name=optimise_levenberg_marquardt) ===
def optimise_levenberg_marquardt(x, a, c, damping=0.001, tolerance=0.001):
    """
    Optimise value of x using levenberg-marquardt
    """
    while True:
        J = calculate_jacobian(x, a, c)
        residual = calculate_residual(x, a, c)
        delta_x = -np.linalg.inv(J.T @ J + damping * np.eye(J.shape[1])) @ J.T @ residual
        if np.linalg.norm(delta_x) < tolerance:
            break
        x += delta_x

    return x

# === BLOCK 4 (label=lm, source_idx=line1832_lm, name=perform) ===
def perform(self):
        """
        Performs a simple HTTP request against the configured url and returns
        true if the response has a 2xx code.

        The url can be configured to use https via the "https" boolean flag
        in the config, as well as a custom HTTP method via the "method" key.

        The default is to not use https and the GET method.
        """
        url = self.config['url']
        if self.config.get('https', False):
            url = url.replace('http://', 'https://')
        method = self.config.get('method', 'GET')

        request = urllib.request.Request(url, method=method)
        response = urllib.request.urlopen(request)
        return response.code // 100 == 2

# === BLOCK 5 (label=human, source_idx=line4281_human, name=wait_until) ===
def wait_until(predicate, timeout=30):
    """Wait until predicate returns a truthy value or the timeout is reached.

    >>> wait_until(lambda: True, timeout=10)
    """
    not_expired = Timeout(timeout)
    while not_expired():
        r = predicate()
        if r:
            break

# === BLOCK 6 (label=lm, source_idx=line2236_lm, name=acos) ===
def acos(x):
    """
    Inverse cosine
    """
    return math.acos(x)
