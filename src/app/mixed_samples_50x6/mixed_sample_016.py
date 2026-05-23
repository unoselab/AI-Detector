# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line325_human, name=main) ===
def main():
    """Invoked by the script installed by setuptools."""
    parser.name('tinman')
    parser.description(__desc__)

    p = parser.get()
    p.add_argument('-p', '--path',
                   action='store',
                   dest='path',
                   help='Path to prepend to the Python system path')

    helper.start(Controller)

# === BLOCK 2 (label=human, source_idx=line1199_human, name=get_type_id) ===
def get_type_id(context, **kw):
    """Returns the type id for the context passed in
    """
    portal_type = kw.get("portal_type", None)
    if portal_type:
        return portal_type

    # Override by provided marker interface
    if IAnalysisRequestPartition.providedBy(context):
        return "AnalysisRequestPartition"
    elif IAnalysisRequestRetest.providedBy(context):
        return "AnalysisRequestRetest"
    elif IAnalysisRequestSecondary.providedBy(context):
        return "AnalysisRequestSecondary"

    return api.get_portal_type(context)

# === BLOCK 3 (label=lm, source_idx=line1874_lm, name=wait) ===
def wait(self, timeout=None):
        """
        Block until the container stops, then return its exit code. Similar to
        the ``podman wait`` command.

        :param timeout: int, microseconds to wait before polling for completion
        :return: int, exit code
        """
        if timeout is not None:
            timeout = timeout / 1000000  # Convert microseconds to seconds

        while True:
            status = self.client.containers.get(self.id).status
            if status == "exited":
                exit_code = self.client.containers.get(self.id).attrs["State"]["ExitCode"]
                return exit_code
            time.sleep(timeout)

# === BLOCK 4 (label=lm, source_idx=line2275_lm, name=ignore_comments) ===
def ignore_comments(lines_enum):
    # type: (ReqFileLines) -> ReqFileLines
    """
    Strips comments and filter empty lines.
    """
    return (
        line.split("#")[0].strip() for line in lines_enum if line.split("#")[0].strip()
    )

# === BLOCK 5 (label=human, source_idx=line1658_human, name=open) ===
def open(self):
        """Start. Multiple calls have no effect.

        Not safe to call from multiple threads at once.
        """
        with self._lock:
            if self._thread_will_exit:
                # If the background thread has read self._stopped as True
                # there is a chance that it has not yet exited. The call to
                # join should not block indefinitely because there is no
                # other work done outside the while loop in self._run.
                try:
                    self._thread.join()
                except ReferenceError:
                    # Thread terminated.
                    pass
            self._thread_will_exit = False
            self._stopped = False
        started = False
        try:
            started = self._thread and self._thread.is_alive()
        except ReferenceError:
            # Thread terminated.
            pass

        if not started:
            thread = threading.Thread(target=self._run, name=self._name)
            thread.daemon = True
            self._thread = weakref.proxy(thread)
            _register_executor(self)
            thread.start()

# === BLOCK 6 (label=lm, source_idx=line273_lm, name=wait) ===
def wait(rh):
    """
    Wait for the virtual machine to go into the specified state.

    Input:
       Request Handle with the following properties:
          function    - 'POWERVM'
          subfunction - 'WAIT'
          userid      - userid of the virtual machine
          parms['desiredState']   - Desired state
          parms['maxQueries']     - Maximum number of queries to issue
          parms['maxWait']        - Maximum time to wait in seconds
          parms['poll']           - Polling interval in seconds

    Output:
       Request Handle updated with the results.
       Return code - 0: ok, non-zero: error
    """
    desired_state = rh.parms['desiredState']
    max_queries = rh.parms['maxQueries']
    max_wait = rh.parms['maxWait']
    poll = rh.parms['poll']
    current_state = get_current_state()
    while current_state!= desired_state and max_queries > 0:
        time.sleep(poll)
        current_state = get_current_state()
        max_queries -= 1
    if current_state == desired_state:
        return 0
    else:
        return 1
