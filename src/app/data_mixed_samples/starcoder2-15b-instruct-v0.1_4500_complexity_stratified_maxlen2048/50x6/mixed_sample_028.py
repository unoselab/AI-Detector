# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line284_human, name=needs_quotes) ===
def needs_quotes(s):
    """Checks whether a string is a dot language ID.
    It will check whether the string is solely composed
    by the characters allowed in an ID or not.
    If the string is one of the reserved keywords it will
    need quotes too but the user will need to add them
    manually.
    """
    # If the name is a reserved keyword it will need quotes but pydot
    # can't tell when it's being used as a keyword or when it's simply
    # a name. Hence the user needs to supply the quotes when an element
    # would use a reserved keyword as name. This function will return
    # false indicating that a keyword string, if provided as-is, won't
    # need quotes.
    if s in DOT_KEYWORDS:
        return False
    chars = [ord(c) for c in s if ord(c)>0x7f or ord(c)==0]
    if chars and not ID_RE_DBL_QUOTED.match(s) and not ID_RE_HTML.match(s):
        return True
    for test_re in [ID_RE_ALPHA_NUMS, ID_RE_NUM, ID_RE_DBL_QUOTED, ID_RE_HTML, ID_RE_ALPHA_NUMS_WITH_PORTS]:
        if test_re.match(s):
            return False
    m = ID_RE_WITH_PORT.match(s)
    if m:
        return needs_quotes(m.group(1)) or needs_quotes(m.group(2))
    return True

# === BLOCK 2 (label=lm, source_idx=line871_lm, name=receive_message) ===
def receive_message(self, message, data):
        """ Called when a media message is received. """
        if message =='media_received':
            print(f"Media received: {data}")
        elif message =='media_not_received':
            print(f"Media not received: {data}")
        else:
            print(f"Unknown message: {message}")

# === BLOCK 3 (label=human, source_idx=line2677_human, name=get_details) ===
def get_details(app_url=defaults.APP_URL):
    """
    returns environment details for the app url specified

    """
    url = '%s/environment' % app_url
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        raise JutException('Unable to retrieve environment details from %s, got %s: %s' %
                           (url, response.status_code, response.text))

# === BLOCK 4 (label=human, source_idx=line3891_human, name=optimise_levenberg_marquardt) ===
def optimise_levenberg_marquardt(x, a, c, damping=0.001, tolerance=0.001):
    """
    Optimise value of x using levenberg-marquardt
    """
    x_new = x
    x_old = x-1 # dummy value
    f_old = f(x_new, a, c)
    while np.abs(x_new - x_old).sum() > tolerance:
        x_old = x_new
        x_tmp = levenberg_marquardt_update(x_old, a, c, damping)
        f_new = f(x_tmp, a, c)
        if f_new < f_old:
            damping = np.max(damping/10., 1e-20)
            x_new = x_tmp
            f_old = f_new
        else:
            damping *= 10.
    return x_new

# === BLOCK 5 (label=lm, source_idx=line378_lm, name=centroid_refine_triangulation_by_triangles) ===
def centroid_refine_triangulation_by_triangles(self, triangles):
        """
        return points defining a refined triangulation obtained by bisection of all edges
        in the triangulation that are associated with the triangles in the list provided.

        Notes
        -----
         The triangles are here represented as a single index.
         The vertices of triangle i are given by self.simplices[i].
        """
        refined_simplices = []
        for triangle in triangles:
            vertices = self.simplices[triangle]
            centroid = np.mean(vertices, axis=0)
            refined_simplices.append(centroid)
        return refined_simplices

# === BLOCK 6 (label=lm, source_idx=line4626_lm, name=reboot) ===
def reboot(name, call=None):
    """
    reboot a server by name
    :param name: name given to the machine
    :param call: call value in this case is 'action'
    :return: true if successful

    CLI Example:

    .. code-block:: bash

        salt-cloud -a reboot vm_name
    """
    if call!= 'action':
        return False
    return True
