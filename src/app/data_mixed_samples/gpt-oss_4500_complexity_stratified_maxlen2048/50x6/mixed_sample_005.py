# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3632_human, name=start_editing) ===
def start_editing(self, treeview, event):
        """Make the treeview grab the focus and start editing the cell
        that the user has clicked to avoid confusion with two or three
        clicks before editing a keybinding.

        Thanks to gnome-keybinding-properties.c =)
        """
        x, y = int(event.x), int(event.y)
        ret = treeview.get_path_at_pos(x, y)
        if not ret:
            return False

        path, column, cellx, celly = ret

        treeview.row_activated(path, Gtk.TreeViewColumn(None))
        treeview.set_cursor(path)

        return False

# === BLOCK 2 (label=lm, source_idx=line3097_lm, name=DFS) ===
def DFS(G):
    """
    Algorithm for depth-first searching the vertices of a graph.
    """
    visited = set()
    order = []

    def _dfs(v):
        visited.add(v)
        order.append(v)
        for w in G.get(v, []):
            if w not in visited:
                _dfs(w)

    for vertex in G:
        if vertex not in visited:
            _dfs(vertex)

    return order

# === BLOCK 3 (label=human, source_idx=line924_human, name=removeUrl) ===
def removeUrl(self, url):
        """Remove passed url from a binder
        """

        root = self.etree
        t_urls = root.find('urls')

        if not t_urls:
            return False

        for t_url in t_urls.findall('url'):
            if t_url.text == url.strip():
                t_urls.remove(t_url)
                if url in self.urls:
                    self.urls.remove(url)
                return True

        return False

# === BLOCK 4 (label=lm, source_idx=line6963_lm, name=resolve) ===
def resolve(var, context):
    """
    Resolve the variable, or return the value passed to it in the first place
    """
    if isinstance(var, str):
        parts = var.split('.')
        cur = context
        for part in parts:
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                try:
                    cur = getattr(cur, part)
                except Exception:
                    return var
        return cur
    return var

# === BLOCK 5 (label=lm, source_idx=line5473_lm, name=_tls_auth_decrypt) ===
def _tls_auth_decrypt(self, s):
        """
        Provided with the record header and AEAD-ciphered data, return the
        sliced and clear tuple (TLSInnerPlaintext, tag). Note that
        we still return the slicing of the original input in case of decryption
        failure. Also, if the integrity check fails, a warning will be issued,
        but we still return the sliced (unauthenticated) plaintext.
        """

# === BLOCK 6 (label=human, source_idx=line3788_human, name=calc_deviation) ===
def calc_deviation(values, average):
    """
    Calculate the standard deviation of a list of values
    @param values: list(float)
    @param average:
    @return:
    """
    size = len(values)
    if size < 2:
        return 0
    calc_sum = 0.0

    for number in range(0, size):
        calc_sum += math.sqrt((values[number] - average) ** 2)
    return math.sqrt((1.0 / (size - 1)) * (calc_sum / size))
