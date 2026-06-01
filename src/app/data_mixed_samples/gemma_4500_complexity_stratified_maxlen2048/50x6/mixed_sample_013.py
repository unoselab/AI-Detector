# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line7033_lm, name=format_survival_rate) ===
def format_survival_rate():
    """cr-rate

    Usage: cr-rate <session-file>

    Calculate the survival rate of a session.
    """
    import sys

    if len(sys.argv) < 2:
        return

    try:
        with open(sys.argv[1], 'r') as f:
            lines = f.readlines()

        total = 0
        survived = 0
        for line in lines:
            if line.strip():
                total += 1
                if "survived" in line.lower():
                    survived += 1

        rate = (survived / total * 100) if total > 0 else 0
        print(f"Survival Rate: {rate:.2f}%")
    except FileNotFoundError:
        print("Error: Session file not found.")

# === BLOCK 2 (label=human, source_idx=line266_human, name=engineer_info) ===
def engineer_info(self, action):

        """
        Returns:
            dict: engineer command information
                - arguments (list<dict>): command arguments
                    - args (list):  args to pass through to click.argument
                    - kwargs (dict): keyword arguments to pass through to click.argument
                - options (list<dict>): command options
                    - args (list):  args to pass through to click.option
                    - kwargs (dict): keyword options to pass through to click.option
        """

        fn = getattr(self, action, None)
        if not fn:
            raise AttributeError("Engineer action not found: %s" % action)
        if not hasattr(fn, "engineer"):
            raise AttributeError("Engineer action not exposed: %s" % action)

        return fn.engineer

# === BLOCK 3 (label=human, source_idx=line8772_human, name=get) ===
async def get(self, file_stream, pid, vendor_specific=None):
        """MNRead.get()

        Retrieve the SciObj bytes and write them to a file or other stream.

        Args:
            file_stream: Open file-like object
                Stream to which the SciObj bytes will be written.

            pid: str

            vendor_specific: dict
                Custom HTTP headers to include in the request

        See also:
            MNRead.get().

        """
        async with await self._retry_request(
            "get", ["object", pid], vendor_specific=vendor_specific
        ) as response:
            self._assert_valid_response(response)
            async for chunk_str, _ in response.content.iter_chunks():
                file_stream.write(chunk_str)

# === BLOCK 4 (label=lm, source_idx=line5426_lm, name=reload_dependencies) ===
def reload_dependencies(force=False):
    """
    Reloads all python modules that law depends on. Currently, this is just *luigi* and *six*.
    Unless *force* is *True*, multiple calls to this function will not have any effect.
    """
    if not force:
        if hasattr(reload_dependencies, "_called"):
            return
        reload_dependencies._called = True

    import importlib
    import luigi
    import six
    importlib.reload(luigi)
    importlib.reload(six)

# === BLOCK 5 (label=lm, source_idx=line7711_lm, name=add_wikipage) ===
def add_wikipage(self, slug, content, **attrs):
        """
        Add a Wiki page to the project and returns a :class:`WikiPage` object.

        :param name: name of the :class:`WikiPage`
        :param attrs: optional attributes for :class:`WikiPage`
        """
        page = self.WikiPage(slug=slug, content=content, **attrs)
        self.pages[slug] = page
        return page

# === BLOCK 6 (label=human, source_idx=line721_human, name=commit) ===
def commit(self):
        """
        :param tag:
            Checks out specified commit.
            If set to ``None`` the latest commit will be checked out
        :returns:
            A list of all commits, descending
        """

        commit = self._log(num=-1, format='%H')
        if commit.get('returncode') == 0:
            return commit.get('stdout')
