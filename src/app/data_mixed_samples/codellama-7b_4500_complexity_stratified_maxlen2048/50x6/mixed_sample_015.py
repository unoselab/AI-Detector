# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2612_lm, name=process_signal) ===
def process_signal(self, signum):
        """Invoked whenever a signal is added to the stack.

        :param int signum: The signal that was added

        """
        if signum == signal.SIGINT:
            self.logger.info("SIGINT received, shutting down")
            self.shutdown()
        elif signum == signal.SIGTERM:
            self.logger.info("SIGTERM received, shutting down")
            self.shutdown()
        elif signum == signal.SIGHUP:
            self.logger.info("SIGHUP received, reloading configuration")
            self.reload()
        elif signum == signal.SIGUSR1:
            self.logger.info("SIGUSR1 received, dumping stack traces")
            self.dump_stack_traces()
        elif signum == signal.SIGUSR2:
            self.logger.info("SIGUSR2 received, dumping process info")
            self.dump_process_info()
        else:
            self.logger.info("Signal %s received, ignoring", signum)

# === BLOCK 2 (label=human, source_idx=line2075_human, name=create_files) ===
def create_files(filedef, cleanup=True):
    """Contextmanager that creates a directory structure from a yaml
       descripttion.
    """
    cwd = os.getcwd()
    tmpdir = tempfile.mkdtemp()
    try:
        Filemaker(tmpdir, filedef)
        if not cleanup:  # pragma: nocover
            pass
            # print("TMPDIR =", tmpdir)
        os.chdir(tmpdir)
        yield tmpdir
    finally:
        os.chdir(cwd)
        if cleanup:  # pragma: nocover
            shutil.rmtree(tmpdir, ignore_errors=True)

# === BLOCK 3 (label=lm, source_idx=line5724_lm, name=find_videos_by_playlist) ===
def find_videos_by_playlist(self, playlist_id, page=1, count=20):
        """doc: http://open.youku.com/docs/doc?id=71
        """
        params = {
            'client_id': self.client_id,
            'page': page,
            'count': count,
            'id': playlist_id,
            'type': 'playlist',
        }
        return self.get('playlist/video/list', params)

# === BLOCK 4 (label=human, source_idx=line3920_human, name=elXpath) ===
def elXpath(self, xpath, dom=None):
        """check if element is present by css"""
        if dom is None:
            dom = self.browser
        return expect(dom.is_element_present_by_xpath, args=[xpath])

# === BLOCK 5 (label=human, source_idx=line5476_human, name=pop) ===
def pop(self, name):
        """Get and remove key from database (atomic)."""
        name = mkey(name)
        temp = mkey((name, "__poptmp__"))
        self.rename(name, temp)
        value = self[temp]
        del(self[temp])
        return value

# === BLOCK 6 (label=lm, source_idx=line1026_lm, name=abort) ===
def abort(self):
        """
        Handle request to cancel HTTP call
        """
        self.log.debug("abort")
        self.abort_flag = True
        self.log.debug("abort done")
