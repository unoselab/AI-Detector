# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1874_human, name=wait) ===
def wait(self, timeout=None):
        """
        Block until the container stops, then return its exit code. Similar to
        the ``podman wait`` command.

        :param timeout: int, microseconds to wait before polling for completion
        :return: int, exit code
        """
        timeout = ["--interval=%s" % timeout] if timeout else []
        cmdline = ["podman", "wait"] + timeout + [self._id or self.get_id()]
        return run_cmd(cmdline, return_output=True)

# === BLOCK 2 (label=lm, source_idx=line2825_lm, name=pex_hash) ===
def pex_hash(cls, d):
    """Return a reproducible hash of the contents of a directory."""
    hasher = hashlib.sha256()
    for root, dirs, files in os.walk(d):
        for file in files:
            with open(os.path.join(root, file), 'rb') as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    hasher.update(data)
    return hasher.hexdigest()

# === BLOCK 3 (label=lm, source_idx=line2068_lm, name=_translate_pattern) ===
def _translate_pattern(self, pattern, anchor=True, prefix=None,
                           is_regex=False):
        """Translate a shell-like wildcard pattern to a compiled regular
        expression.

        Return the compiled regex.  If 'is_regex' true,
        then 'pattern' is directly compiled to a regex (if it's a string)
        or just returned as-is (assumes it's a regex object).
        """
        def _translate_pattern(self, pattern, anchor=True, prefix=None, is_regex=False):
            if is_regex:
                if isinstance(pattern, str):
                    return re.compile(pattern)
                else:
                    return pattern
            else:
                regex = fnmatch.translate(pattern)
                if anchor:
                    regex = r'^' + regex + r'$'
                if prefix:
                    regex = prefix + regex
                return re.compile(regex)

# === BLOCK 4 (label=lm, source_idx=line1658_lm, name=open) ===
def open(self):
        """Start. Multiple calls have no effect.

        Not safe to call from multiple threads at once.
        """
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run)
            self._thread.start()

# === BLOCK 5 (label=human, source_idx=line2451_human, name=get_asset_notification_session) ===
def get_asset_notification_session(self, asset_receiver):
        """Gets the notification session for notifications pertaining to asset changes.

        arg:    asset_receiver (osid.repository.AssetReceiver): the
                notification callback
        return: (osid.repository.AssetNotificationSession) - an
                ``AssetNotificationSession``
        raise:  NullArgument - ``asset_receiver`` is ``null``
        raise:  OperationFailed - unable to complete request
        raise:  Unimplemented - ``supports_asset_notification()`` is
                ``false``
        *compliance: optional -- This method must be implemented if
        ``supports_asset_notification()`` is ``true``.*

        """
        if not self.supports_asset_notification():
            raise errors.Unimplemented()
        # pylint: disable=no-member
        return sessions.AssetNotificationSession(runtime=self._runtime, receiver=asset_receiver)

# === BLOCK 6 (label=human, source_idx=line2314_human, name=extract_to_disk) ===
def extract_to_disk(self):
        """Extract all files and write them to disk."""
        archive_name, extension = os.path.splitext(os.path.basename(self.file.name))
        if not os.path.isdir(os.path.join(os.getcwd(), archive_name)):
            os.mkdir(archive_name)
        os.chdir(archive_name)
        for filename, data in self.extract().items():
            f = open(filename, 'wb')
            f.write(data or b'')
            f.close()
