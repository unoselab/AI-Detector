# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4282_human, name=insert) ===
def insert(self, context):

		"""
		Applies database changes.

		:param resort.engine.execution.Context context:
		   Current execution context.
		"""

		script_path = context.resolve(self.__script_path)
		buf = io.StringIO()
		self.__preprocess(script_path, buf)
		buf.seek(0)
		self.__conn.execute(buf.read())

# === BLOCK 2 (label=human, source_idx=line8461_human, name=from_dict) ===
def from_dict(cls, val):
        """Creates dict2 object from dict object

        Args:
            val (:obj:`dict`): Value to create from

        Returns:
            Equivalent dict2 object.
        """
        if isinstance(val, dict2):
            return val

        elif isinstance(val, dict):
            res = cls()
            for k, v in val.items():
                res[k] = cls.from_dict(v)
            return res

        elif isinstance(val, list):
            res = []
            for item in val:
                res.append(cls.from_dict(item))
            return res
        else:
            return val

# === BLOCK 3 (label=lm, source_idx=line8859_lm, name=put_task) ===
def put_task(self, dp, callback=None):
        """
        Same as in :meth:`AsyncPredictorBase.put_task`.
        """
        return self._predictor.put_task(dp, callback)

# === BLOCK 4 (label=lm, source_idx=line2656_lm, name=expand_region) ===
def expand_region(tuple_of_s, a, b, start=0, stop=None):
    """Apply expend_slice on a tuple of slices"""
    if stop is None:
        stop = len(a)
    return tuple(expand_slice(s, a, b, start, stop) for s in tuple_of_s)

# === BLOCK 5 (label=lm, source_idx=line6715_lm, name=iter_intersecting) ===
def iter_intersecting(self, iterable, key=None, descending=False):
        """Like `iter_intersect_test`, but returns intersections only.

        Returns:
            An iterator that returns items from `iterable` that intersect.
        """
        return self._iter_intersect_test(
            iterable, key=key, descending=descending, intersecting=True
        )

# === BLOCK 6 (label=human, source_idx=line1438_human, name=move_to_element) ===
def move_to_element(self, to_element):
        """
        Moving the mouse to the middle of an element.

        :Args:
         - to_element: The WebElement to move to.
        """
        if self._driver.w3c:
            self.w3c_actions.pointer_action.move_to(to_element)
            self.w3c_actions.key_action.pause()
        else:
            self._actions.append(lambda: self._driver.execute(
                                 Command.MOVE_TO, {'element': to_element.id}))
        return self
