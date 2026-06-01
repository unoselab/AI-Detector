# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line7904_lm, name=setposition) ===
def setposition(self, position):
        """
        The move format is in long algebraic notation.

        Takes list of stirngs = ['e2e4', 'd7d5']
        OR
        FEN = 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1'
        """
        if isinstance(position, list):
            for move in position:
                self.move(move)
        elif isinstance(position, str):
            self.setfen(position)
        else:
            raise ValueError('Position must be a list or a string')

# === BLOCK 2 (label=lm, source_idx=line7635_lm, name=expected_number_of_purchases_up_to_time) ===
def expected_number_of_purchases_up_to_time(self, t):
        """
        Return expected number of repeat purchases up to time t.

        Calculate the expected number of repeat purchases up to time t for a
        randomly choose individual from the population.

        Parameters
        ----------
        t: array_like
            times to calculate the expectation for.

        Returns
        -------
        array_like

        """
        return self.expected_number_of_purchases_up_to_time_for_individual(
            self.random_individual(), t)

# === BLOCK 3 (label=human, source_idx=line4401_human, name=pubsub_channels) ===
def pubsub_channels(self, pattern=None):
        """Lists the currently active channels."""
        args = [b'PUBSUB', b'CHANNELS']
        if pattern is not None:
            args.append(pattern)
        return self.execute(*args)

# === BLOCK 4 (label=lm, source_idx=line6330_lm, name=_identify_heterogeneity_blocks_seg) ===
def _identify_heterogeneity_blocks_seg(in_file, seg_file, params, work_dir, somatic_info):
    """Identify heterogeneity blocks corresponding to segmentation from CNV input file.
    """
    out_file = os.path.join(work_dir, "heterogeneity_blocks.seg")
    if not os.path.exists(out_file):
        cmd = "python {0} -i {1} -s {2} -o {3} -p {4}".format(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "identify_heterogeneity_blocks_seg.py"),
            in_file, seg_file, out_file, params)
        subprocess.check_call(cmd, shell=True)
    return out_file

# === BLOCK 5 (label=human, source_idx=line1821_human, name=_not_in) ===
def _not_in(x, y):
    """Compute the vectorized membership of ``x not in y`` if possible,
    otherwise use Python.
    """
    try:
        return ~x.isin(y)
    except AttributeError:
        if is_list_like(x):
            try:
                return ~y.isin(x)
            except AttributeError:
                pass
        return x not in y

# === BLOCK 6 (label=human, source_idx=line5519_human, name=add_variable) ===
def add_variable(self, variable, card=0):
        """
        Add a variable to the model.

        Parameters:
        -----------
        variable: any hashable python object

        card: int
            Representing the cardinality of the variable to be added.

        Examples:
        ---------
        >>> from pgmpy.models import MarkovChain as MC
        >>> model = MC()
        >>> model.add_variable('x', 4)
        """
        if variable not in self.variables:
            self.variables.append(variable)
        else:
            warn('Variable {var} already exists.'.format(var=variable))
        self.cardinalities[variable] = card
        self.transition_models[variable] = {}
