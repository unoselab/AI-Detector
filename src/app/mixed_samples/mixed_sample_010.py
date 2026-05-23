# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1449_human, name=_handle_event) ===
def _handle_event(self, connection, event):
        """
        Handle an Event event incoming on ServerConnection connection.
        """
        with self.mutex:
            matching_handlers = sorted(
                self.handlers.get("all_events", [])
                + self.handlers.get(event.type, [])
            )
            for handler in matching_handlers:
                result = handler.callback(connection, event)
                if result == "NO MORE":
                    return

# === BLOCK 2 (label=human, source_idx=line890_human, name=backend) ===
def backend(self, client=None):
        """The :class:`stdnet.BackendDatServer` for this instance.

        It can be ``None``.
        """
        session = self.session
        if session:
            return session.model(self).backend

# === BLOCK 3 (label=human, source_idx=line667_human, name=receive_message) ===
def receive_message(self):
        """Receive a message from the transport.

        Blocks until a message has been received. May return a context
        opaque to clients that should be passed to :py:func:`send_reply`
        to identify the client later on.

        :return: A tuple consisting of ``(context, message)``.
        """

        if not ('REQUEST_METHOD' in os.environ
                and os.environ['REQUEST_METHOD'] == 'POST'):
            print("Status: 405 Method not Allowed; only POST is accepted")
            exit(0)

        # POST
        content_length = int(os.environ['CONTENT_LENGTH'])
        request_json = sys.stdin.read(content_length)
        request_json = urlparse.unquote(request_json)
        # context isn't used with cgi
        return None, request_json

# === BLOCK 4 (label=human, source_idx=line2511_human, name=toNoUintArray) ===
def toNoUintArray(arr):
    """
    cast array to the next higher integer array
    if dtype=unsigned integer
    """
    d = arr.dtype
    if d.kind == 'u':
        arr = arr.astype({1: np.int16,
                          2: np.int32,
                          4: np.int64}[d.itemsize])
    return arr
