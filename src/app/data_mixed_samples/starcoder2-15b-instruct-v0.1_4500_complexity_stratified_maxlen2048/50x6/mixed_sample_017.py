# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1733_lm, name=group_attrib) ===
def group_attrib(self):
        """
        return a namedtuple containing all attributes attached
        to groups of which the given series is a member
        for each group of which the series is a member
        """
        GroupAttrib = namedtuple('GroupAttrib', ['name', 'value'])
        group_attribs = []
        for group in self.groups():
            group_attribs.append(GroupAttrib(group.name, group.attrib))
        return group_attribs

# === BLOCK 2 (label=lm, source_idx=line3202_lm, name=atlas_make_zonefile_inventory) ===
def atlas_make_zonefile_inventory( bit_offset, bit_length, con=None, path=None ):
    """
    Get a summary description of the list of zonefiles we have
    for the given block range (a "zonefile inventory")

    Zonefile present/absent bits are ordered left-to-right,
    where the leftmost bit is the earliest zonefile in the blockchain.

    Offset and length are in bytes.

    This is slow.  Use the in-RAM zonefile inventory vector whenever possible
    (see atlas_get_zonefile_inventory).
    """
    if con is None:
        con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM zonefiles WHERE offset >=? AND offset + length <=?",
        (bit_offset, bit_offset + bit_length),
    )
    num_present = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM zonefiles WHERE offset >=? AND offset <?",
        (bit_offset, bit_offset + bit_length),
    )
    num_partial = cur.fetchone()[0]
    return (num_present, num_partial - num_present, bit_length - num_partial)

# === BLOCK 3 (label=lm, source_idx=line1134_lm, name=stddev_samples) ===
def stddev_samples(data, xcol, ycollist, delta=1.0):
    """Create a sample list that contains the mean and standard deviation of the original list. Each element in the returned list contains following values: [MEAN, STDDEV, MEAN - STDDEV*delta, MEAN + STDDEV*delta].

>>> chart_data.stddev_samples([ [1, 10, 15, 12, 15], [2, 5, 10, 5, 10], [3, 32, 33, 35, 36], [4,16,66, 67, 68] ], 0, range(1,5))
[(1, 13.0, 2.1213203435596424, 10.878679656440358, 15.121320343559642), (2, 7.5, 2.5, 5.0, 10.0), (3, 34.0, 1.5811388300841898, 32.418861169915807, 35.581138830084193), (4, 54.25, 22.094965489902897, 32.155034510097103, 76.344965489902904)]
"""
    samples = []
    for row in data:
        x = row[xcol]
        ylist = [row[ycol] for ycol in ycollist]
        mean = sum(ylist) / len(ylist)
        stddev = (sum((y - mean) ** 2 for y in ylist) / len(ylist)) ** 0.5
        samples.append((x, mean, stddev, mean - stddev * delta, mean + stddev * delta))
    return samples

# === BLOCK 4 (label=human, source_idx=line4502_human, name=_serialization_helper) ===
def _serialization_helper(self, ray_forking):
        """This is defined in order to make pickling work.

        Args:
            ray_forking: True if this is being called because Ray is forking
                the actor handle and false if it is being called by pickling.

        Returns:
            A dictionary of the information needed to reconstruct the object.
        """
        if ray_forking:
            actor_handle_id = compute_actor_handle_id(
                self._ray_actor_handle_id, self._ray_actor_forks)
        else:
            actor_handle_id = self._ray_actor_handle_id

        # Note: _ray_actor_cursor and _ray_actor_creation_dummy_object_id
        # could be None.
        state = {
            "actor_id": self._ray_actor_id,
            "actor_handle_id": actor_handle_id,
            "module_name": self._ray_module_name,
            "class_name": self._ray_class_name,
            "actor_cursor": self._ray_actor_cursor,
            "actor_method_names": self._ray_actor_method_names,
            "method_signatures": self._ray_method_signatures,
            "method_num_return_vals": self._ray_method_num_return_vals,
            # Actors in local mode don't have dummy objects.
            "actor_creation_dummy_object_id": self.
            _ray_actor_creation_dummy_object_id,
            "actor_method_cpus": self._ray_actor_method_cpus,
            "actor_driver_id": self._ray_actor_driver_id,
            "ray_forking": ray_forking
        }

        if ray_forking:
            self._ray_actor_forks += 1
            new_actor_handle_id = actor_handle_id
        else:
            # The execution dependency for a pickled actor handle is never safe
            # to release, since it could be unpickled and submit another
            # dependent task at any time. Therefore, we notify the backend of a
            # random handle ID that will never actually be used.
            new_actor_handle_id = ActorHandleID(_random_string())
        # Notify the backend to expect this new actor handle. The backend will
        # not release the cursor for any new handles until the first task for
        # each of the new handles is submitted.
        # NOTE(swang): There is currently no garbage collection for actor
        # handles until the actor itself is removed.
        self._ray_new_actor_handles.append(new_actor_handle_id)

        return state

# === BLOCK 5 (label=human, source_idx=line2931_human, name=_select_theory) ===
def _select_theory(theories):
        """Return the most likely spacing convention given different options.

        Given a dictionary of convention options as keys and their occurrence
        as values, return the convention that occurs the most, or ``None`` if
        there is no clear preferred style.
        """
        if theories:
            values = tuple(theories.values())
            best = max(values)
            confidence = float(best) / sum(values)
            if confidence > 0.5:
                return tuple(theories.keys())[values.index(best)]

# === BLOCK 6 (label=human, source_idx=line3867_human, name=_tidy_stacktrace) ===
def _tidy_stacktrace(stack):
    """
    Clean up stacktrace and remove all entries that:
    1. Are part of Django (except contrib apps)
    2. Are part of SocketServer (used by Django's dev server)
    3. Are the last entry (which is part of our stacktracing code)

    ``stack`` should be a list of frame tuples from ``inspect.stack()``
    """
    django_path = os.path.realpath(os.path.dirname(django.__file__))
    django_path = os.path.normpath(os.path.join(django_path, '..'))
    socketserver_path = os.path.realpath(os.path.dirname(SocketServer.__file__))
    pymongo_path = os.path.realpath(os.path.dirname(pymongo.__file__))

    trace = []
    for frame, path, line_no, func_name, text in (f[:5] for f in stack):
        s_path = os.path.realpath(path)
        # Support hiding of frames -- used in various utilities that provide
        # inspection.
        if '__traceback_hide__' in frame.f_locals:
            continue
        if getattr(settings, 'DEBUG_TOOLBAR_CONFIG', {}).get('HIDE_DJANGO_SQL', True) \
            and django_path in s_path and not 'django/contrib' in s_path:
            continue
        if socketserver_path in s_path:
            continue
        if pymongo_path in s_path:
            continue
        if not text:
            text = ''
        else:
            text = (''.join(text)).strip()
        trace.append((path, line_no, func_name, text))
    return trace
