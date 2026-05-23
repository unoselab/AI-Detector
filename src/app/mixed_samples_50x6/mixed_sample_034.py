# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1514_lm, name=sympy_expressions_equal) ===
def sympy_expressions_equal(expr1, expr2):
    """
    Compare two sympy expressions that are not necessarily expanded.
    :param expr1: a first expression
    :param expr2: a second expression
    :return: True if the expressions are similar, False otherwise
    """
    return expand(expr1) == expand(expr2)

# === BLOCK 2 (label=human, source_idx=line2813_human, name=_get_names) ===
def _get_names(self):
        """Get the list of first names.

        :return: A list of first name entries.
        """
        names = self._read_name_file('names.json')
        names = self._compute_weights(names)

        return names

# === BLOCK 3 (label=lm, source_idx=line2560_lm, name=percentile) ===
def percentile(self, percentile):
        """Return bin center nearest to percentile"""
        if percentile < 0 or percentile > 100:
            raise ValueError("Percentile must be between 0 and 100")
        cumulative_sum = 0
        for bin_center, bin_count in self.bins.items():
            cumulative_sum += bin_count
            if cumulative_sum >= percentile:
                return bin_center
        return None

# === BLOCK 4 (label=human, source_idx=line2155_human, name=_handle_chat_name) ===
def _handle_chat_name(self, data):
        """Handle user name changes"""

        self.room.user.nick = data
        self.conn.enqueue_data("user", self.room.user)

# === BLOCK 5 (label=human, source_idx=line2803_human, name=remove_bad_sequence) ===
def remove_bad_sequence(codon_list, bad_seq, bad_seqs):
    """
    Make a silent mutation to the given codon list to remove the first instance 
    of the given bad sequence found in the gene sequence.  If the bad sequence 
    isn't found, nothing happens and the function returns false.  Otherwise the 
    function returns true.  You can use these return values to easily write a 
    loop totally purges the bad sequence from the codon list.  Both the 
    specific bad sequence in question and the list of all bad sequences are 
    expected to be regular expressions.
    """

    gene_seq = ''.join(codon_list)
    problem = bad_seq.search(gene_seq)

    if not problem:
        return False

    bs_start_codon = problem.start() // 3
    bs_end_codon = problem.end() // 3

    for i in range(bs_start_codon, bs_end_codon):
        problem_codon = codon_list[i]
        amino_acid = translate_dna(problem_codon)

        alternate_codons = [
                codon
                for codon in dna.ecoli_reverse_translate[amino_acid]
                if codon != problem_codon]

        for alternate_codon in alternate_codons:
            codon_list[i] = alternate_codon

            if problem_with_codon(i, codon_list, bad_seqs):
                codon_list[i] = problem_codon
            else:
                return True

    raise RuntimeError("Could not remove bad sequence '{}' from gene.".format(bs))

# === BLOCK 6 (label=lm, source_idx=line328_lm, name=login_user) ===
def login_user(user, remember=None):
    """Perform the login routine.

    If SECURITY_TRACKABLE is used, make sure you commit changes after this
    request (i.e. ``app.security.datastore.commit()``).

    :param user: The user to login
    :param remember: Flag specifying if the remember cookie should be set.
                     Defaults to ``False``
    """
    if remember is None:
        remember = False
    app.security.login_user(user, remember=remember)
