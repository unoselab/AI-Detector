# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3559_human, name=chord_counts) ===
def chord_counts(im):
    r"""
    Finds the length of each chord in the supplied image and returns a list
    of their individual sizes

    Parameters
    ----------
    im : ND-array
        An image containing chords drawn in the void space.

    Returns
    -------
    result : 1D-array
        A 1D array with one element for each chord, containing its length.

    Notes
    ----
    The returned array can be passed to ``plt.hist`` to plot the histogram,
    or to ``sp.histogram`` to get the histogram data directly. Another useful
    function is ``sp.bincount`` which gives the number of chords of each
    length in a format suitable for ``plt.plot``.
    """
    labels, N = spim.label(im > 0)
    props = regionprops(labels, coordinates='xy')
    chord_lens = sp.array([i.filled_area for i in props])
    return chord_lens

# === BLOCK 2 (label=lm, source_idx=line2086_lm, name=insertFromMimeData) ===
def insertFromMimeData(self, source):
        """
        Inserts the information from the inputed source.

        :param      source | <QMimeData>
        """
        mime_data = source
        if mime_data.hasText():
            text = mime_data.text()
            self.insertPlainText(text)
        elif mime_data.hasHtml():
            html = mime_data.html()
            self.insertHtml(html)

# === BLOCK 3 (label=human, source_idx=line595_human, name=set_sessid) ===
def set_sessid(sessid):
    """
    Save this current sessid in ``$HOME/.profrc``
    """
    filename = path.join(path.expanduser('~'), '.profrc')
    config = configparser.ConfigParser()
    config.read(filename)
    config.set('DEFAULT', 'Session', sessid)
    with open(filename, 'w') as configfile:
        print("write a new sessid")
        config.write(configfile)

# === BLOCK 4 (label=human, source_idx=line5416_human, name=get_tmpdir) ===
def get_tmpdir():
    """
    On first invocation, creates a temporary directory and returns its
    path. Subsequent invocations uses the same directory.

    :returns: A temporary directory created for this run of glerbl.
    :rtype: :class:`str`
    """
    global __tmpdir
    if __tmpdir is not None:
        return __tmpdir

    __tmpdir = tempfile.mkdtemp(prefix='.tmp.glerbl.', dir=".")
    atexit.register(__clean_tmpdir)

    return __tmpdir

# === BLOCK 5 (label=lm, source_idx=line3184_lm, name=rcs) ===
def rcs(J,P,R,T,p,c,a,RUB):
    """rcs -- model for the resource constrained scheduling problem
    Parameters:
        - J: set of jobs
        - P: set of precedence constraints between jobs
        - R: set of resources
        - T: number of periods
        - p[j]: processing time of job j
        - c[j,t]: cost incurred when job j starts processing on period t.
        - a[j,r,t]: resource r usage for job j on period t (after job starts)
        - RUB[r,t]: upper bound for resource r on period t
    Returns a model, ready to be solved.
    """
    from pulp import LpProblem, LpVariable, lpSum, LpMinimize

    model = LpProblem("RCSP", LpMinimize)

    # x[j, t] = 1 if job j starts at time t
    x = LpVariable.dicts("x", [(j, t) for j in J for t in range(T)], cat="Binary")

    # Objective: Minimize total cost
    model += lpSum(c[j, t] * x[j, t] for j in J for t in range(T))

    # Constraint 1: Each job must start exactly once
    for j in J:
        model += lpSum(x[j, t] for t in range(T)) == 1

    # Constraint 2: Precedence constraints (j, k) in P means j must finish before k starts
    for (j, k) in P:
        model += lpSum(t * x[j, t] for t in range(T)) + p[j] <= lpSum(t * x[k, t] for t in range(T))

    # Constraint 3: Resource constraints for each resource r at each time t
    for r in R:
        for t in range(T):
            # Job j uses resource r at time t if it started at time s such that s <= t < s + p[j]
            # The resource usage is a[j, r, t-s] where t-s is the relative time since start
            model += lpSum(x[j, s] * a[j, r, t - s]
                           for j in J
                           for s in range(max(0, t - p[j] + 1), t + 1)
                           if (j, r, t - s) in a) <= RUB[r, t]

    return model

# === BLOCK 6 (label=lm, source_idx=line2091_lm, name=_nearest) ===
async def _nearest(
            self,
            kind: str,
            latitude: Union[float, str] = None,
            longitude: Union[float, str] = None) -> dict:
        """Return data from nearest city/station (IP or coordinates)."""
        if latitude is None or longitude is None:
            import requests
            resp = requests.get("https://ipapi.co/json/").json()
            latitude = resp.get("latitude")
            longitude = resp.get("longitude")

        import requests
        url = f"https://api.openweathermap.org/data/2.5/{kind}"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
