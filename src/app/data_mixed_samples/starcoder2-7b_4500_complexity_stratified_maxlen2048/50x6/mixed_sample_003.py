# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line5764_human, name=_set_vibration_win) ===
def _set_vibration_win(self, left_motor, right_motor, duration):
        """Control the motors on Windows."""
        self._start_vibration_win(left_motor, right_motor)
        stop_process = Process(target=delay_and_stop,
                               args=(duration,
                                     self.manager.xinput_dll,
                                     self.__device_number))
        stop_process.start()

# === BLOCK 2 (label=lm, source_idx=line2756_lm, name=tomof) ===
def tomof(self, indent=0, maxline=MAX_MOF_LINE):
        """
        Return a MOF string with the declaration of this CIM method for use in
        a CIM class declaration.

        The order of parameters and qualifiers is preserved.

        Parameters:

          indent (:term:`integer`): Number of spaces to indent each line of
            the returned string, counted in the line with the method name.

        Returns:

          :term:`unicode string`: MOF string.
        """
        if self.is_static:
            return self.name + " : " + self.return_type + " = " + \
                self.return_type + ".static." + self.name + \
                self.get_parameters_as_mof(indent=indent, maxline=maxline)
        else:
            return self.name + " : " + self.return_type + " = " + \
                self.return_type + "." + self.name + \
                self.get_parameters_as_mof(indent=indent, maxline=maxline)

# === BLOCK 3 (label=human, source_idx=line6216_human, name=save_state_regularly) ===
def save_state_regularly(self, fname, frequency=600):
        """
        Save the state of node with a given regularity to the given
        filename.

        Args:
            fname: File name to save retularly to
            frequency: Frequency in seconds that the state should be saved.
                        By default, 10 minutes.
        """
        self.save_state(fname)
        loop = asyncio.get_event_loop()
        self.save_state_loop = loop.call_later(frequency,
                                               self.save_state_regularly,
                                               fname,
                                               frequency)

# === BLOCK 4 (label=human, source_idx=line6136_human, name=setPollFDNotifiers) ===
def setPollFDNotifiers(
            self, added_cb=None, removed_cb=None, user_data=None):
        """
        Give libusb1 methods to call when it should add/remove file descriptor
        for polling.
        You should not have to call this method, unless you are integrating
        this class with a polling mechanism.
        """
        if added_cb is None:
            added_cb = self.__null_pointer
        else:
            added_cb = libusb1.libusb_pollfd_added_cb_p(added_cb)
        if removed_cb is None:
            removed_cb = self.__null_pointer
        else:
            removed_cb = libusb1.libusb_pollfd_removed_cb_p(removed_cb)
        if user_data is None:
            user_data = self.__null_pointer
        self.__added_cb = added_cb
        self.__removed_cb = removed_cb
        self.__poll_cb_user_data = user_data
        self.__libusb_set_pollfd_notifiers(
            self.__context_p,
            self.__cast(added_cb, libusb1.libusb_pollfd_added_cb_p),
            self.__cast(removed_cb, libusb1.libusb_pollfd_removed_cb_p),
            user_data,
        )

# === BLOCK 5 (label=lm, source_idx=line4154_lm, name=iter_singleton_referents_tuples) ===
def iter_singleton_referents_tuples(self):
        """
        Iterator of all of the singleton members's id number of the context set.

        NOTE: this evaluates entities one-at-a-time, and does not handle relational constraints.
        """
        for entity in self.iter_entities():
            for member in entity.iter_members():
                if member.is_singleton():
                    yield (entity.id, member.id)

# === BLOCK 6 (label=lm, source_idx=line5077_lm, name=route_not_found) ===
def route_not_found(*args):
        """
        Constructs a Flask Response for when a API Route (path+method) is not found. This is usually
        HTTP 404 but with API Gateway this is a HTTP 403 (https://forums.aws.amazon.com/thread.jspa?threadID=2166840)

        :return: a Flask Response
        """
        return flask.Response(status=403, response="Route not found")
