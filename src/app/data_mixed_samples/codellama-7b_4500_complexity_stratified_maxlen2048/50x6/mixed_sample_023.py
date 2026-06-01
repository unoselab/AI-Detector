# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3563_human, name=pdf_mmd) ===
def pdf_mmd(self, lon, lat, mag_1, mag_2, distance_modulus, mask, delta_mag=0.03, steps=1000):
        """
        Ok, now here comes the beauty of having the signal MMD.
        """
        logger.info('Running MMD pdf')

        roi = mask.roi
        mmd = self.signalMMD(mask,distance_modulus,delta_mag=delta_mag,mass_steps=steps)

        # This is fragile, store this information somewhere else...
        nedges = np.rint((roi.bins_mag[-1]-roi.bins_mag[0])/delta_mag)+1
        edges_mag,delta_mag = np.linspace(roi.bins_mag[0],roi.bins_mag[-1],nedges,retstep=True)

        idx_mag_1 = np.searchsorted(edges_mag,mag_1)
        idx_mag_2 = np.searchsorted(edges_mag,mag_2)

        if np.any(idx_mag_1 > nedges) or np.any(idx_mag_1 == 0):
            msg = "Magnitude out of range..."
            raise Exception(msg)
        if np.any(idx_mag_2 > nedges) or np.any(idx_mag_2 == 0):
            msg = "Magnitude out of range..."
            raise Exception(msg)

        idx = mask.roi.indexROI(lon,lat)
        u_color = mmd[(mask.mask_roi_digi[idx],idx_mag_1,idx_mag_2)]

        # Remove the bin size to convert the pdf to units of mag^-2
        u_color /= delta_mag**2

        return u_color

# === BLOCK 2 (label=lm, source_idx=line2019_lm, name=updateLodState) ===
def updateLodState(self, verbose=None):
        """
        Switch between full graphics details <---> fast rendering mode.

        Returns a success message.

        :param verbose: print more

        :returns: 200: successful operation
        """
        if verbose is None:
            verbose = self._verbose
        if verbose:
            print("updateLodState")
        return self._updateLodState(verbose=verbose)

# === BLOCK 3 (label=human, source_idx=line6074_human, name=get_eol) ===
def get_eol(self):
        """Read the next token and raise an exception if it isn't EOL or
        EOF.

        @raises dns.exception.SyntaxError:
        @rtype: string
        """

        token = self.get()
        if not token.is_eol_or_eof():
            raise dns.exception.SyntaxError('expected EOL or EOF, got %d "%s"' % (token.ttype, token.value))
        return token.value

# === BLOCK 4 (label=human, source_idx=line5402_human, name=setModelData) ===
def setModelData(self, editor, model, index):
        """
        Updates the item with the new data value.

        :param      editor  | <QtGui.QWidget>
                    model   | <QtGui.QModel>
                    index   | <QtGui.QModelIndex>
        """
        value = editor.currentText()
        model.setData(index, wrapVariant(value))

# === BLOCK 5 (label=lm, source_idx=line3176_lm, name=read_sj_out_tab) ===
def read_sj_out_tab(filename):
    """Read an SJ.out.tab file as produced by the RNA-STAR aligner into a
    pandas Dataframe.

    Parameters
    ----------
    filename : str of filename or file handle
        Filename of the SJ.out.tab file you want to read in

    Returns
    -------
    sj : pandas.DataFrame
        Dataframe of splice junctions

    """
    if isinstance(filename, str):
        f = open(filename)
    else:
        f = filename

    sj = pd.read_csv(f, sep='\t', header=None, names=['chrom', 'start', 'end', 'strand', 'gene_id', 'sj_id', 'sj_score', 'sj_type'])
    f.close()

    return sj

# === BLOCK 6 (label=lm, source_idx=line2042_lm, name=_RegisterFlowProcessingHandler) ===
def _RegisterFlowProcessingHandler(self, handler):
    """Registers a handler to receive flow processing messages."""
    self._flow_processing_handlers.append(handler)
