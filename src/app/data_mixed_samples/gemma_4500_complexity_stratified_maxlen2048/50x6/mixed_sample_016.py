# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line613_lm, name=get_changeform_initial_data) ===
def get_changeform_initial_data(self, request):
        """
        Provide initial datas when creating an entry.
        """
        initial_data = {}
        if 'initial' in request.GET:
            import json
            try:
                initial_data = json.loads(request.GET.get('initial', '{}'))
            except (ValueError, TypeError):
                pass
        return initial_data

# === BLOCK 2 (label=human, source_idx=line7317_human, name=get_least_relevant_words_for_topic) ===
def get_least_relevant_words_for_topic(vocab, rel_mat, topic, n=None):
    """
    Get words from `vocab` for `topic` ordered by least to most relevance (Sievert and Shirley 2014) using the relevance
    matrix `rel_mat` obtained from `get_topic_word_relevance()`.
    Optionally only return the `n` least relevant words.
    """
    _check_relevant_words_for_topic_args(vocab, rel_mat, topic)
    return _words_by_score(vocab, rel_mat[topic], least_to_most=True, n=n)

# === BLOCK 3 (label=lm, source_idx=line7258_lm, name=sample_bad_readout) ===
def sample_bad_readout(program, num_samples, assignment_probs, cxn):
    """
    Generate `n` samples of measuring all outcomes of a Quil `program`
    assuming the assignment probabilities `assignment_probs` by simulating the
    wave function on a qvm QVMConnection `cxn`

    :param pyquil.quil.Program program: The program.
    :param int num_samples: The number of samples
    :param numpy.ndarray assignment_probs: A matrix of assignment probabilities
    :param QVMConnection cxn: the QVM connection.
    :return: The resulting sampled outcomes from assignment_probs applied to cxn, one dimensional.
    :rtype: numpy.ndarray
    """
    import numpy as np

    # Get the ideal state probabilities from the QVM
    ideal_probs = cxn.run(program, execute_shots=0)

    # The ideal_probs is typically a dictionary or array of probabilities
    # We need to ensure it is a vector aligned with assignment_probs
    # If ideal_probs is a dict, convert to array based on the size of assignment_probs
    if isinstance(ideal_probs, dict):
        ideal_vec = np.zeros(assignment_probs.shape[0])
        for state, prob in ideal_probs.items():
            # Convert binary string state to integer index
            idx = int(state, 2)
            ideal_vec[idx] = prob
    else:
        ideal_vec = np.array(ideal_probs)

    # Calculate the actual probabilities: P(observed) = sum_i P(observed|ideal_i) * P(ideal_i)
    # assignment_probs[i, j] is P(observed=i | ideal=j)
    actual_probs = np.dot(assignment_probs, ideal_vec)

    # Normalize to ensure it sums to 1 (handling floating point precision)
    actual_probs /= np.sum(actual_probs)

    # Sample from the resulting distribution
    outcomes = np.arange(len(actual_probs))
    samples = np.random.choice(outcomes, size=num_samples, p=actual_probs)

    return samples

# === BLOCK 4 (label=lm, source_idx=line3144_lm, name=setup) ===
def setup(self, target_directory=None):  # pylint: disable=arguments-differ
    """Sets up the _target_directory attribute.

    Args:
      target_directory: Directory in which collected files will be dumped.
    """
    self._target_directory = target_directory

# === BLOCK 5 (label=human, source_idx=line7489_human, name=_create_join_index) ===
def _create_join_index(self, index, other_index, indexer,
                           other_indexer, how='left'):
        """
        Create a join index by rearranging one index to match another

        Parameters
        ----------
        index: Index being rearranged
        other_index: Index used to supply values not found in index
        indexer: how to rearrange index
        how: replacement is only necessary if indexer based on other_index

        Returns
        -------
        join_index
        """
        join_index = index.take(indexer)
        if (self.how in (how, 'outer') and
                not isinstance(other_index, MultiIndex)):
            # if final index requires values in other_index but not target
            # index, indexer may hold missing (-1) values, causing Index.take
            # to take the final value in target index
            mask = indexer == -1
            if np.any(mask):
                # if values missing (-1) from target index,
                # take from other_index instead
                join_list = join_index.to_numpy()
                other_list = other_index.take(other_indexer).to_numpy()
                join_list[mask] = other_list[mask]
                join_index = Index(join_list, dtype=join_index.dtype,
                                   name=join_index.name)
        return join_index

# === BLOCK 6 (label=human, source_idx=line4006_human, name=unpack_fixed16) ===
def unpack_fixed16(src):
    """Get a FIXED16 value (called plainly FIXED in the spec)."""
    dec_part = unpack_ui16(src)
    int_part = unpack_ui16(src)
    return int_part + dec_part / 65536
