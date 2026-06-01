# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1683_human, name=master_main) ===
def master_main(painter, router, select, delay):
    """
    Loop until CTRL+C is pressed, waiting for the next result delivered by the
    Select. Use parse_output() to turn that result ('ps' command output) into
    rich data, and finally repaint the screen if the repaint delay has passed.
    """
    next_paint = 0
    while True:
        msg = select.get()
        parse_output(msg.receiver.host, msg.unpickle())
        if next_paint < time.time():
            next_paint = time.time() + delay
            painter.paint()

# === BLOCK 2 (label=lm, source_idx=line4101_lm, name=loadZone) ===
def loadZone(self, zone, callback=None, errback=None):
        """
        Load an existing zone into a high level Zone object.

        :param str zone: zone name, like 'example.com'
        :rtype: :py:class:`ns1.zones.Zone`
        """
        return self.client.loadZone(zone, callback, errback)

# === BLOCK 3 (label=human, source_idx=line3473_human, name=moving_average) ===
def moving_average(data, periods, type='simple'):
    """
    compute a <periods> period moving average.
    type is 'simple' | 'exponential'
    """
    data = np.asarray(data)
    if type == 'simple':
        weights = np.ones(periods)
    else:
        weights = np.exp(np.linspace(-1., 0., periods))

    weights /= weights.sum()

    mavg = np.convolve(data, weights, mode='full')[:len(data)]
    mavg[:periods] = mavg[periods]
    return mavg

# === BLOCK 4 (label=lm, source_idx=line629_lm, name=_strptime) ===
def _strptime(expr, date_format):
    """
    Return datetimes specified by date_format,
    which supports the same string format as the python standard library.
    Details of the string format can be found in python string format doc

    :param expr:
    :param date_format: date format string (e.g. “%Y-%m-%d”)
    :type date_format: str
    :return:
    """
    return datetime.strptime(expr, date_format)

# === BLOCK 5 (label=lm, source_idx=line8108_lm, name=show_top_losses) ===
def show_top_losses(self, k:int, max_len:int=70)->None:
        """
        Create a tabulation showing the first `k` texts in top_losses along with their prediction, actual,loss, and probability of
        actual class. `max_len` is the maximum number of tokens displayed.
        """
        if k>len(self.top_losses):
            k=len(self.top_losses)
        for i in range(k):
            print(f"{i+1:>2d}. {self.top_losses[i][0][:max_len]}")
            print(f"    Prediction: {self.top_losses[i][1]}")
            print(f"    Actual: {self.top_losses[i][2]}")
            print(f"    Loss: {self.top_losses[i][3]:.4f}")
            print(f"    Probability: {self.top_losses[i][4]:.4f}")
            print()

# === BLOCK 6 (label=human, source_idx=line6431_human, name=add_sub_directory) ===
def add_sub_directory(self, key, path):
        """Adds a sub-directory to the results directory.

        Parameters
        ----------
        key: str
            A look-up key for the directory path.
        path: str
            The relative path from the root of the results directory to the sub-directory.

        Returns
        -------
        str:
            The absolute path to the sub-directory.
        """
        sub_dir_path = os.path.join(self.results_root, path)
        os.makedirs(sub_dir_path, exist_ok=True)
        self._directories[key] = sub_dir_path
        return sub_dir_path
