# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line5101_lm, name=register) ===
def register(self, CorpNum, cashbill, UserID=None):
        """ 현금영수증 등록
            args
                CorpNum : 팝빌회원 사업자번호
                cashbill : 등록할 현금영수증 object. made with Cashbill(...)
                UserID : 팝빌회원 아이디
            return
                처리결과. consist of code and message
            raise
                PopbillException
        """

# === BLOCK 2 (label=human, source_idx=line5836_human, name=fit) ===
def fit(self, vecs, iter=20, seed=123):
        """Given training vectors, run k-means for each sub-space and create
        codewords for each sub-space.

        This function should be run once first of all.

        Args:
            vecs (np.ndarray): Training vectors with shape=(N, D) and dtype=np.float32.
            iter (int): The number of iteration for k-means
            seed (int): The seed for random process

        Returns:
            object: self

        """
        assert vecs.dtype == np.float32
        assert vecs.ndim == 2
        N, D = vecs.shape
        assert self.Ks < N, "the number of training vector should be more than Ks"
        assert D % self.M == 0, "input dimension must be dividable by M"
        self.Ds = int(D / self.M)

        np.random.seed(seed)
        if self.verbose:
            print("iter: {}, seed: {}".format(iter, seed))

        # [m][ks][ds]: m-th subspace, ks-the codeword, ds-th dim
        self.codewords = np.zeros((self.M, self.Ks, self.Ds), dtype=np.float32)
        for m in range(self.M):
            if self.verbose:
                print("Training the subspace: {} / {}".format(m, self.M))
            vecs_sub = vecs[:, m * self.Ds : (m+1) * self.Ds]
            self.codewords[m], _ = kmeans2(vecs_sub, self.Ks, iter=iter, minit='points')

        return self

# === BLOCK 3 (label=lm, source_idx=line5753_lm, name=change_hosts) ===
def change_hosts(self, mode, host_family, host, onerror = None):
        """mode is either X.HostInsert or X.HostDelete. host_family is
        one of X.FamilyInternet, X.FamilyDECnet or X.FamilyChaos.

        host is a list of bytes. For the Internet family, it should be the
        four bytes of an IPv4 address."""

# === BLOCK 4 (label=lm, source_idx=line2654_lm, name=is_named_tuple) ===
def is_named_tuple(cls):
    """Return True if cls is a namedtuple and False otherwise."""
    if not isinstance(cls, type):
        return False
    if not issubclass(cls, tuple):
        return False
    fields = getattr(cls, "_fields", None)
    return isinstance(fields, tuple)

# === BLOCK 5 (label=human, source_idx=line5977_human, name=_upsert_run) ===
def _upsert_run(self, retry, storage_id, env):
        """Upsert the Run (ie. for the first time with all its attributes)

        Arguments:
            retry: (bool) Whether to retry if the connection fails (ie. if the backend is down).
                False is useful so we can start running the user process even when the W&B backend
                is down, and let syncing finish later.
        Returns:
            True if the upsert succeeded, False if it failed because the backend is down.
        Throws:
            LaunchError on other failures
        """
        if retry:
            num_retries = None
        else:
            num_retries = 0  # no retries because we want to let the user process run even if the backend is down

        try:
            upsert_result = self._run.save(
                id=storage_id, num_retries=num_retries, api=self._api)
        except wandb.apis.CommError as e:
            logger.exception("communication error with wandb %s" % e.exc)
            # TODO: Get rid of str contains check
            if self._run.resume == 'never' and 'exists' in str(e):
                raise LaunchError(
                    "resume='never' but run (%s) exists" % self._run.id)
            else:
                # Detect bad request code -- this is usually trying to
                # create a run that has been already deleted
                if (isinstance(e.exc, requests.exceptions.HTTPError) and
                    e.exc.response.status_code == 400):
                    raise LaunchError(
                        'Failed to connect to W&B. See {} for details.'.format(
                        util.get_log_file_path()))

                if isinstance(e.exc, (requests.exceptions.HTTPError,
                                      requests.exceptions.Timeout,
                                      requests.exceptions.ConnectionError)):
                    wandb.termerror(
                        'Failed to connect to W&B. Retrying in the background.')
                    return False

                launch_error_s = 'Launch exception: {}, see {} for details.  To disable wandb set WANDB_MODE=dryrun'.format(e, util.get_log_file_path())
                if 'Permission denied' in str(e):
                    launch_error_s += '\nRun "wandb login", or provide your API key with the WANDB_API_KEY environment variable.'

                raise LaunchError(launch_error_s)

        if self._output:
            url = self._run.get_url(self._api)
            wandb.termlog("Syncing to %s" % url)
            wandb.termlog("Run `wandb off` to turn off syncing.")

        self._run.set_environment(environment=env)

        logger.info("saving patches")
        self._api.save_patches(self._watch_dir)
        logger.info("saving pip packages")
        self._api.save_pip(self._watch_dir)
        logger.info("initializing streaming files api")
        self._api.get_file_stream_api().set_file_policy(
            OUTPUT_FNAME, CRDedupeFilePolicy())
        self._api.get_file_stream_api().start()
        self._project = self._api.settings("project")

        # unblock file syncing and console streaming, which need the Run to have a .storage_id
        logger.info("unblocking file change observer, beginning sync with W&B servers")
        self._unblock_file_observer()

        return True

# === BLOCK 6 (label=human, source_idx=line3383_human, name=resolve_meta_key) ===
def resolve_meta_key(hub, key, meta):
    """ Resolve a value when it's a string and starts with '>' """
    if key not in meta:
        return None
    value = meta[key]
    if isinstance(value, str) and value[0] == '>':
        topic = value[1:]
        if topic not in hub:
            raise KeyError('topic %s not found in hub' % topic)
        return hub[topic].get()
    return value
