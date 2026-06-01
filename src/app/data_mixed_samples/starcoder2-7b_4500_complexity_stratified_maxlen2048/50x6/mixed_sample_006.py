# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3782_lm, name=get_field_type) ===
def get_field_type(f):
    """Obtain the type name of a GRPC Message field."""
    return f.type_name.split('.')[-1]

# === BLOCK 2 (label=human, source_idx=line799_human, name=EnqueueBreakpointUpdate) ===
def EnqueueBreakpointUpdate(self, breakpoint):
    """Asynchronously updates the specified breakpoint on the backend.

    This function returns immediately. The worker thread is actually doing
    all the work. The worker thread is responsible to retry the transmission
    in case of transient errors.

    Args:
      breakpoint: breakpoint in either final or non-final state.
    """
    with self._transmission_thread_startup_lock:
      if self._transmission_thread is None:
        self._transmission_thread = threading.Thread(
            target=self._TransmissionThreadProc)
        self._transmission_thread.name = 'Cloud Debugger transmission thread'
        self._transmission_thread.daemon = True
        self._transmission_thread.start()

    self._transmission_queue.append((breakpoint, 0))
    self._new_updates.set()

# === BLOCK 3 (label=lm, source_idx=line5727_lm, name=row_cells) ===
def row_cells(self, row_idx):
        """
        Sequence of cells in the row at *row_idx* in this table.
        """
        return self.rows[row_idx]

# === BLOCK 4 (label=human, source_idx=line5156_human, name=findXAt) ===
def findXAt(xArr, yArr, yVal, index=0, s=0.0):
    """
    index: position of root (return index=0 by default)

    return all x values where y would be equal to given yVal
    if arrays are spline interpolated
    """
    if xArr[1] < xArr[0]:
        # numbers must be in ascending order, otherwise method crashes...
        xArr = xArr[::-1]
        yArr = yArr[::-1]

    yArr = yArr - yVal
    if len(yArr) < 5:
        xn = np.linspace(xArr[0], xArr[-1], 5)
        yArr = np.interp(xn, xArr, yArr)
        xArr = xn
    f = interpolate.UnivariateSpline(xArr, yArr, s=s)
    return f.roots()[index]

# === BLOCK 5 (label=human, source_idx=line3228_human, name=_analyze) ===
def _analyze(self):
        """Convert a few elementary fields into a molecule object"""
        if ("Atomic numbers" in self.fields) and ("Current cartesian coordinates" in self.fields):
            self.molecule = Molecule(
                self.fields["Atomic numbers"],
                np.reshape(self.fields["Current cartesian coordinates"], (-1, 3)),
                self.title,
            )

# === BLOCK 6 (label=lm, source_idx=line5644_lm, name=image_amplitude) ===
def image_amplitude(self, kwargs_ps, kwargs_lens, k=None):
        """
        returns the image amplitudes

        :param kwargs_ps:
        :param kwargs_lens:
        :return:
        """
        if k is None:
            k = self.k
        return self.image_amp_from_source(kwargs_ps, kwargs_lens, k=k)
