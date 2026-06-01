# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2171_human, name=__store_config) ===
def __store_config(self, args, kwargs):
        """ Assign args to kwargs and store configuration. """
        signature = (
            'schema',
            'ignore_none_values',
            'allow_unknown',
            'require_all',
            'purge_unknown',
            'purge_readonly',
        )
        for i, p in enumerate(signature[: len(args)]):
            if p in kwargs:
                raise TypeError("__init__ got multiple values for argument " "'%s'" % p)
            else:
                kwargs[p] = args[i]
        self._config = kwargs

# === BLOCK 2 (label=human, source_idx=line3070_human, name=write) ===
def write(self, obj: BioCDocument or BioCPassage or BioCSentence):
        """
        Encode and write a single object.

        Args:
            obj: an instance of BioCDocument, BioCPassage, or BioCSentence

        Returns:

        """
        if self.level == DOCUMENT and not isinstance(obj, BioCDocument):
            raise ValueError
        if self.level == PASSAGE and not isinstance(obj, BioCPassage):
            raise ValueError
        if self.level == SENTENCE and not isinstance(obj, BioCSentence):
            raise ValueError
        self.writer.write(BioCJSONEncoder().default(obj))

# === BLOCK 3 (label=lm, source_idx=line6805_lm, name=get_instance) ===
def get_instance(self, payload):
        """
        Build an instance of ChallengeInstance

        :param dict payload: Payload response from the API

        :returns: twilio.rest.authy.v1.service.entity.factor.challenge.ChallengeInstance
        :rtype: twilio.rest.authy.v1.service.entity.factor.challenge.ChallengeInstance
        """
        return ChallengeInstance(self._version, payload, service_sid=self._solution['service_sid'], )

# === BLOCK 4 (label=lm, source_idx=line6_lm, name=isiterable) ===
def isiterable(element, exclude=None):
    """Check whatever or not if input element is an iterable.

    :param element: element to check among iterable types.
    :param type/tuple exclude: not allowed types in the test.

    :Example:

    >>> isiterable({})
    True
    >>> isiterable({}, exclude=dict)
    False
    >>> isiterable({}, exclude=(dict,))
    False
    """
    if exclude is None:
        exclude = ()
    if not isinstance(exclude, tuple):
        exclude = (exclude,)
    return isinstance(element, Iterable) and not isinstance(element, exclude)

# === BLOCK 5 (label=lm, source_idx=line3216_lm, name=_generate_relative_positions_embeddings) ===
def _generate_relative_positions_embeddings(length_q, length_k, depth,
                                            max_relative_position, name,
                                            cache=False):
  """Generates tensor of size [1 if cache else length_q, length_k, depth]."""

# === BLOCK 6 (label=human, source_idx=line3726_human, name=tarfile_extract) ===
def tarfile_extract(fileobj, dest_path):
        """Extract a tarfile described by a file object to a specified path.

        Args:
            fileobj (file): File object wrapping the target tarfile.
            dest_path (str): Path to extract the contents of the tarfile to.
        """
        # Though this method doesn't fit cleanly into the TarPartition object,
        # tarballs are only ever extracted for partitions so the logic jives
        # for the most part.
        tar = tarfile.open(mode='r|', fileobj=fileobj,
                           bufsize=pipebuf.PIPE_BUF_BYTES)

        # canonicalize dest_path so the prefix check below works
        dest_path = os.path.realpath(dest_path)

        # list of files that need fsyncing
        extracted_files = []

        # Iterate through each member of the tarfile individually. We must
        # approach it this way because we are dealing with a pipe and the
        # getmembers() method will consume it before we extract any data.
        for member in tar:
            assert not member.name.startswith('/')
            relpath = os.path.join(dest_path, member.name)

            # Workaround issue with tar handling of symlink, see:
            # https://bugs.python.org/issue12800
            if member.issym():
                target_path = os.path.join(dest_path, member.name)
                try:
                    os.symlink(member.linkname, target_path)
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        os.remove(target_path)
                        os.symlink(member.linkname, target_path)
                    else:
                        raise
                continue

            if member.isreg() and member.size >= pipebuf.PIPE_BUF_BYTES:
                cat_extract(tar, member, relpath)
            else:
                tar.extract(member, path=dest_path)

            filename = os.path.realpath(relpath)
            extracted_files.append(filename)

            # avoid accumulating an unbounded list of strings which
            # could be quite large for a large database
            if len(extracted_files) > 1000:
                _fsync_files(extracted_files)
                del extracted_files[:]
        tar.close()
        _fsync_files(extracted_files)
