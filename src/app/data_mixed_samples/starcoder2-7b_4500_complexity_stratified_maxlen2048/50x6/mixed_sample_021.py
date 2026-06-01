# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line11_human, name=get_visual_content) ===
def get_visual_content(self, id_or_uri):
        """
        Gets a list of visual content objects describing each rack within the data center. The response aggregates data
        center and rack data with a specified metric (peak24HourTemp) to provide simplified access to display data for
        the data center.

        Args:
            id_or_uri: Can be either the resource ID or the resource URI.

        Return:
            list: List of visual content objects.
        """
        uri = self._client.build_uri(id_or_uri) + "/visualContent"
        return self._client.get(uri)

# === BLOCK 2 (label=lm, source_idx=line6988_lm, name=get_advances_declines) ===
def get_advances_declines(self, as_json=False):
        """
        :return: a list of dictionaries with advance decline data
        :raises: URLError, HTTPError
        """
        url = self.base_url + self.advances_declines_url
        response = self.get_response(url)
        if as_json:
            return response.json()
        return response.text

# === BLOCK 3 (label=lm, source_idx=line1589_lm, name=load_user) ===
async def load_user(self, request):
        """Load user from request."""
        user = await self.auth.authenticate(request)
        if user:
            return user
        raise HTTPException(status_code=401, detail="Not authenticated")

# === BLOCK 4 (label=lm, source_idx=line6322_lm, name=_append_seed) ===
def _append_seed(self, seed_type: str, data: Any) -> 'Seeding':
        """Add a seeding method and returns self.

        :returns: self for fluid API
        """
        self._seeds.append((seed_type, data))
        return self

# === BLOCK 5 (label=human, source_idx=line281_human, name=log_debug) ===
def log_debug(msg, logger="TaskLogger"):
    """Log a DEBUG message

    Convenience function to log a message to the default Logger

    Parameters
    ----------
    msg : str
        Message to be logged
    logger : str, optional (default: "TaskLogger")
        Unique name of the logger to retrieve

    Returns
    -------
    logger : TaskLogger
    """
    tasklogger = get_tasklogger(logger)
    tasklogger.debug(msg)
    return tasklogger

# === BLOCK 6 (label=human, source_idx=line5911_human, name=play_NoteContainer) ===
def play_NoteContainer(self, notecontainer):
        """Convert a mingus.containers.NoteContainer to the equivalent MIDI
        events and add it to the track_data.

        Note.channel and Note.velocity can be set as well.
        """
        if len(notecontainer) <= 1:
            [self.play_Note(x) for x in notecontainer]
        else:
            self.play_Note(notecontainer[0])
            self.set_deltatime(0)
            [self.play_Note(x) for x in notecontainer[1:]]
