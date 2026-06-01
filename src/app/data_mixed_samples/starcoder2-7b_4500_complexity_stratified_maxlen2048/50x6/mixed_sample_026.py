# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1601_human, name=clean) ===
def clean(self, initial_epoch):
        """ Remove entries from database that would get overwritten """
        self.db.metrics.delete_many({'run_name': self.model_config.run_name, 'epoch_idx': {'$gt': initial_epoch}})

# === BLOCK 2 (label=human, source_idx=line4881_human, name=clear) ===
def clear(self):
    """Remove all pending events without running any."""
    while self.current or self.idlers or self.queue or self.rpcs:
      current = self.current
      idlers = self.idlers
      queue = self.queue
      rpcs = self.rpcs
      _logging_debug('Clearing stale EventLoop instance...')
      if current:
        _logging_debug('  current = %s', current)
      if idlers:
        _logging_debug('  idlers = %s', idlers)
      if queue:
        _logging_debug('  queue = %s', queue)
      if rpcs:
        _logging_debug('  rpcs = %s', rpcs)
      self.__init__()
      current.clear()
      idlers.clear()
      queue[:] = []
      rpcs.clear()
      _logging_debug('Cleared')

# === BLOCK 3 (label=lm, source_idx=line5806_lm, name=get_email) ===
def get_email(self):
        """Gets email
        :return: Email of user
        """
        return self.email

# === BLOCK 4 (label=human, source_idx=line3209_human, name=is_seq) ===
def is_seq(obj):
    """
    Check if an object is a sequence.
    """
    return (not is_str(obj) and not is_dict(obj) and
            (hasattr(obj, "__getitem__") or hasattr(obj, "__iter__")))

# === BLOCK 5 (label=lm, source_idx=line1974_lm, name=handle) ===
def handle(self, *args, **options):
        """Handle the command"""
        self.stdout.write(self.style.SUCCESS('Successfully created the database'))

# === BLOCK 6 (label=lm, source_idx=line1361_lm, name=point_to_index) ===
def point_to_index(self, point):
        """
        Convert a point to an index in the matrix array.

        Parameters
        ----------
        point: (3,) float, point in space

        Returns
        ---------
        index: (3,) int tuple, index in self.matrix
        """
        index = np.round(point / self.voxel_size).astype(int)
        return tuple(index)
