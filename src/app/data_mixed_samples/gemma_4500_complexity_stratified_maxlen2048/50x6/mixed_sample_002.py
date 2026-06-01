# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line313_lm, name=increment_lessons) ===
def increment_lessons(self, measure_vals, reward_buff_sizes=None):
        """Attempts to increments all the lessons of all the curriculums in this
        MetaCurriculum. Note that calling this method does not guarantee the
        lesson of a curriculum will increment. The lesson of a curriculum will
        only increment if the specified measure threshold defined in the
        curriculum has been reached and the minimum number of episodes in the
        lesson have been completed.

        Args:
            measure_vals (dict): A dict of brain name to measure value.
            reward_buff_sizes (dict): A dict of brain names to the size of their
                corresponding reward buffers.

        Returns:
            A dict from brain name to whether that brain's lesson number was
            incremented.
        """
        incremented = {}
        for brain_name, curriculum in self.curriculums.items():
            if curriculum is None:
                continue

            measure_val = measure_vals.get(brain_name)
            reward_buff_size = reward_buff_sizes.get(brain_name) if reward_buff_sizes else None

            if curriculum.should_increment_lesson(measure_val, reward_buff_size):
                curriculum.increment_lesson()
                incremented[brain_name] = True
            else:
                incremented[brain_name] = False

        return incremented

# === BLOCK 2 (label=lm, source_idx=line1280_lm, name=resolve) ===
def resolve(self, value):
        """Resolves the promise with the given value."""
        if self._state == 'pending':
            self._state = 'resolved'
            self._value = value
            for callback in self._callbacks:
                callback(value)
            self._callbacks = []

# === BLOCK 3 (label=lm, source_idx=line1290_lm, name=__preprocess_arguments) ===
def __preprocess_arguments(root):
    """Preprocesses occurrences of Argument within the root.

    Argument XML values reference other values within the document by name. The
    referenced value does not contain a switch. This function will add the
    switch associated with the argument.
    """
    ref_name = arg.get("name")
    if ref_name:
        referenced = root.find(f".//Argument[@name='{ref_name}']")
        if referenced is not None:
            switch = referenced.get("switch")
            if switch:
                arg.set("switch", switch)

# === BLOCK 4 (label=lm, source_idx=line6348_lm, name=open_recruitment) ===
def open_recruitment(self, n=1):
        """Start recruiting right away."""
        self.recruiting = True
        self.vacancies = n

# === BLOCK 5 (label=lm, source_idx=line1926_lm, name=mount) ===
def mount(self,
              fstype=None,
              options=None,
              auth_no_user_interaction=None):
        """Mount filesystem."""
        if options is None:
            options = []

        params = {
            'fstype': fstype,
            'options': options,
            'auth_no_user_interaction': auth_no_user_interaction
        }

        # Filter out None values to avoid passing them to the underlying system call
        params = {k: v for k, v in params.items() if v is not None}

        return self._execute_mount(**params)

# === BLOCK 6 (label=lm, source_idx=line5077_lm, name=read_octet) ===
def read_octet(self):
        """Read one byte, return as an integer"""
        return ord(self.read(1))
