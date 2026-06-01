# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3506_human, name=expected_information_gain) ===
def expected_information_gain(self, expparams):
        r"""
        Calculates the expected information gain for each hypothetical experiment.

        :param expparams: The experiments at which to compute expected
            information gain.
        :type expparams: :class:`~numpy.ndarray` of dtype given by the current
            model's :attr:`~qinfer.abstract_model.Simulatable.expparams_dtype` property,
            and of shape ``(n,)``

        :return float: The expected information gain for each 
            hypothetical experiment in ``expparams``.
        """
        # This is a special case of the KL divergence estimator (see below),
        # in which the other distribution is guaranteed to share support.

        # for models whose outcome number changes with experiment, we 
        # take the easy way out and for-loop over experiments
        n_eps = expparams.size
        if n_eps > 1 and not self.model.is_n_outcomes_constant:
            risk = np.empty(n_eps)
            for idx in range(n_eps):
                risk[idx] = self.expected_information_gain(expparams[idx, np.newaxis])
            return risk

        # number of outcomes for the first experiment
        os = self.model.domain(expparams[0,np.newaxis])[0].values

        # compute the hypothetical weights, likelihoods and normalizations for
        # every possible outcome and expparam
        # the likelihood over outcomes should sum to 1, so don't compute for last outcome
        w_hyp, L, N = self.hypothetical_update(
                os[:-1], 
                expparams, 
                return_normalization=True, 
                return_likelihood=True
            )
        w_hyp_last_outcome = (1 - L.sum(axis=0)) * self.particle_weights[np.newaxis, :]
        N = np.concatenate([N[:,:,0], np.sum(w_hyp_last_outcome[np.newaxis,:,:], axis=2)], axis=0)
        w_hyp_last_outcome = w_hyp_last_outcome / N[-1,:,np.newaxis]
        w_hyp = np.concatenate([w_hyp, w_hyp_last_outcome[np.newaxis,:,:]], axis=0)
        # w_hyp.shape == (n_out, n_eps, n_particles)
        # N.shape == (n_out, n_eps)

        # compute the Kullback-Liebler divergence for every experiment and possible outcome
        # KLD.shape == (n_out, n_eps)
        KLD = np.sum(w_hyp * np.log(w_hyp / self.particle_weights), axis=2)

        # return the expected KLD (ie expected info gain) for every experiment
        return np.sum(N * KLD, axis=0)

# === BLOCK 2 (label=lm, source_idx=line805_lm, name=SequenceField) ===
def SequenceField(cls, default=NOTHING, required=True, repr=False, key=None):
    """
    Create new sequence field on a model.

    :param cls: class (or name) of the model to be related in Sequence.
    :param default: any TypedSequence or list
    :param bool required: whether or not the object is invalid if not provided.
    :param bool repr: include this field should appear in object's repr.
    :param bool cmp: include this field in generated comparison.
    :param string key: override name of the value when converted to dict.
    """

# === BLOCK 3 (label=human, source_idx=line3328_human, name=count_mismatches) ===
def count_mismatches(read):
    """
    look for NM:i:<N> flag to determine number of mismatches
    """
    if read is False:
        return False
    mm = [int(i.split(':')[2]) for i in read[11:] if i.startswith('NM:i:')]
    if len(mm) > 0:
        return sum(mm)
    else:
        return False

# === BLOCK 4 (label=human, source_idx=line5025_human, name=Process) ===
def Process(self, parser_mediator, zip_file, archive_members):
    """Determines if this is the correct plugin; if so proceed with processing.

    This method checks if the zip file being contains the paths specified in
    REQUIRED_PATHS. If all paths are present, the plugin logic processing
    continues in InspectZipFile.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      zip_file (zipfile.ZipFile): the zip file. It should not be closed in
          this method, but will be closed by the parser logic in czip.py.
      archive_members (list[str]): file paths in the archive.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
      ValueError: if a subclass has not specified REQUIRED_PATHS.
    """
    if not self.REQUIRED_PATHS:
      raise ValueError('REQUIRED_PATHS not specified')

    if not set(archive_members).issuperset(self.REQUIRED_PATHS):
      raise errors.WrongCompoundZIPPlugin(self.NAME)

    logger.debug('Compound ZIP Plugin used: {0:s}'.format(self.NAME))

    self.InspectZipFile(parser_mediator, zip_file)

# === BLOCK 5 (label=lm, source_idx=line4743_lm, name=_read_dataset_metadata) ===
def _read_dataset_metadata(self):
    """Reads dataset metadata.

    Returns:
      instance of DatasetMetadata
    """
    import json
    from pathlib import Path

    metadata_path = getattr(self, "_metadata_path", None)
    if metadata_path is None:
        raise AttributeError("Instance has no attribute '_metadata_path'")

    path = Path(metadata_path)
    if not path.is_file():
        raise FileNotFoundError(f"Metadata file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in metadata file {path}: {exc}") from exc

    return DatasetMetadata(**data)

# === BLOCK 6 (label=lm, source_idx=line5795_lm, name=parse) ===
def parse(stream, with_text=False):  # type: (Iterator[str], bool) -> Iterator[Union[Tuple[str, LexicalUnit], LexicalUnit]]
    """Generates lexical units from a character stream.

    Args:
        stream (Iterator[str]): A character stream containing lexical units, superblanks and other text.
        with_text (Optional[bool]): A boolean defining whether to output preceding text with each lexical unit.

    Yields:
        :class:`LexicalUnit`: The next lexical unit found in the character stream. (if `with_text` is False) \n
        *(str, LexicalUnit)* - The next lexical unit found in the character stream and the the text that seperated it from the
        prior unit in a tuple. (if with_text is True)
    """
