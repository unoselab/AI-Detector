# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line8693_human, name=install) ===
def install(self, destination):
        """ Install a third party odoo add-on

        :param string destination: the folder where the add-on should end up at.
        """
        logger.info(
            "Installing %s@%s to %s",
            self.repo, self.commit if self.commit else self.branch, destination
        )
        with temp_repo(self.repo, self.branch, self.commit) as tmp:
            self._apply_patches(tmp)
            self._move_modules(tmp, destination)

# === BLOCK 2 (label=lm, source_idx=line1504_lm, name=enqueue) ===
def enqueue(self, future):
    """
    Enqueue a future to be processed by one of the threads in the pool.
    The future must be bound to a worker and not have been started yet.
    """
    if future._state != _state.PENDING:
        raise ValueError('future is not pending')
    if future._worker is not None:
        raise ValueError('future is already bound to a worker')
    if future._state == _state.CANCELLED:
        raise ValueError('future is already cancelled')
    if future._state == _state.FINISHED:
        raise ValueError('future is already finished')
    if future._state == _state.CANCELLED:
        raise ValueError('future is already cancelled')

    # Add the future to the queue.
    self._queue.put(future)

    # If we're not already running, start one of the threads.
    if self._processes is None:
        self._processes = []
        for i in range(self._processes_count):
            process = self._ctx.Process(target=self._worker,
                                        args=(self._queue, self._done))
            process.daemon = True
            process.start()
            self._processes.append(process)

# === BLOCK 3 (label=lm, source_idx=line1034_lm, name=_get_property) ===
def _get_property(name):
    """
    Delegate property to self.loop
    """

# === BLOCK 4 (label=lm, source_idx=line5277_lm, name=parse_block) ===
def parse_block(self, block_id, txs):
        """
        Given the sequence of transactions in a block, turn them into a
        sequence of virtual chain operations.

        Return the list of successfully-parsed virtualchain transactions
        """
        vc_txs = []
        for tx in txs:
            try:
                vc_txs.append(self.parse_tx(tx))
            except Exception as e:
                self.logger.error("Failed to parse tx %s: %s", tx, e)
        return vc_txs

# === BLOCK 5 (label=human, source_idx=line430_human, name=from_dict) ===
def from_dict(cls, d):
        """Create cache hierarchy from dictionary."""
        main_memory = MainMemory()
        caches = {}

        referred_caches = set()

        # First pass, create all named caches and collect references
        for name, conf in d.items():
            caches[name] = Cache(name=name,
                                 **{k: v for k, v in conf.items()
                                    if k not in ['store_to', 'load_from', 'victims_to']})
            if 'store_to' in conf:
                referred_caches.add(conf['store_to'])
            if 'load_from' in conf:
                referred_caches.add(conf['load_from'])
            if 'victims_to' in conf:
                referred_caches.add(conf['victims_to'])

        # Second pass, connect caches
        for name, conf in d.items():
            if 'store_to' in conf and conf['store_to'] is not None:
                caches[name].set_store_to(caches[conf['store_to']])
            if 'load_from' in conf and conf['load_from'] is not None:
                caches[name].set_load_from(caches[conf['load_from']])
            if 'victims_to' in conf and conf['victims_to'] is not None:
                caches[name].set_victims_to(caches[conf['victims_to']])

        # Find first level (not target of any load_from or store_to)
        first_level = set(d.keys()) - referred_caches
        assert len(first_level) == 1, "Unable to find first cache level."
        first_level = caches[list(first_level)[0]]

        # Find last level caches (has no load_from or store_to target)
        last_level_load = c = first_level
        while c is not None:
            last_level_load = c
            c = c.load_from
        assert last_level_load is not None, "Unable to find last cache level."
        last_level_store = c = first_level
        while c is not None:
            last_level_store = c
            c = c.store_to
        assert last_level_store is not None, "Unable to find last cache level."

        # Set main memory connections
        main_memory.load_to(last_level_load)
        main_memory.store_from(last_level_store)

        return cls(first_level, main_memory), caches, main_memory

# === BLOCK 6 (label=human, source_idx=line6141_human, name=safe_cd) ===
def safe_cd(path):
    """
    Changes to a directory, yields, and changes back.
    Additionally any error will also change the directory back.

    Usage:
    >>> with safe_cd('some/repo'):
    ...     call('git status')
    """
    starting_directory = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(starting_directory)
