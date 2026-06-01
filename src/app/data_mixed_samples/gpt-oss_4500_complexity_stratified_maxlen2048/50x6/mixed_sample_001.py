# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3051_human, name=coding_sequence) ===
def coding_sequence(self):
        """
        cDNA coding sequence (from start codon to stop codon, without
        any introns)
        """
        if self.sequence is None:
            return None

        start = self.first_start_codon_spliced_offset
        end = self.last_stop_codon_spliced_offset

        # If start codon is the at nucleotide offsets [3,4,5] and
        # stop codon is at nucleotide offsets  [20,21,22]
        # then start = 3 and end = 22.
        #
        # Adding 1 to end since Python uses non-inclusive ends in slices/ranges.

        # pylint: disable=invalid-slice-index
        # TODO(tavi) Figure out pylint is not happy with this slice
        return self.sequence[start:end + 1]

# === BLOCK 2 (label=human, source_idx=line6202_human, name=phi) ===
def phi(self):
        """get the weighted total objective function

        Returns
        -------
        phi : float
            sum of squared residuals

        """
        sum = 0.0
        for grp, contrib in self.phi_components.items():
            sum += contrib
        return sum

# === BLOCK 3 (label=human, source_idx=line1206_human, name=detach) ===
def detach(self):
        """
        Detach the underlying LLVM resource without disposing of it.
        """
        if not self._closed:
            del self._as_parameter_
            self._closed = True
            self._ptr = None

# === BLOCK 4 (label=human, source_idx=line5532_human, name=from_response_data) ===
def from_response_data(cls, response_data):
        """
        Response factory

        :param response_data: requests.models.Response
        :return: pybomb.clients.Response
        """

        response_json = response_data.json()

        return cls(
            response_data.url,
            response_json["number_of_page_results"],
            response_json["number_of_total_results"],
            response_json["results"],
        )

# === BLOCK 5 (label=human, source_idx=line2834_human, name=reset_default) ===
def reset_default(verbose=False):
    """Remove custom.css and custom fonts"""
    paths = [jupyter_custom, jupyter_nbext]

    for fpath in paths:
        custom = '{0}{1}{2}.css'.format(fpath, os.sep, 'custom')
        try:
            os.remove(custom)
        except Exception:
            pass
    try:
        delete_font_files()
    except Exception:
        check_directories()
        delete_font_files()

    copyfile(defaultCSS, jupyter_customcss)
    copyfile(defaultJS, jupyter_customjs)

    if os.path.exists(theme_name_file):
        os.remove(theme_name_file)

    if verbose:
        print("Reset css and font defaults in:\n{} &\n{}".format(*paths))

# === BLOCK 6 (label=human, source_idx=line1887_human, name=status) ===
async def status(cls):
        """
        Returns the current status of the configured API server.
        """
        rqst = Request(cls.session, 'GET', '/manager/status')
        rqst.set_json({
            'status': 'running',
        })
        async with rqst.fetch() as resp:
            return await resp.json()
