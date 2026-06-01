# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1560_lm, name=sampled_logs) ===
def sampled_logs(self, logs_limit=-1):
        """Return up to `logs_limit` logs.

        If `logs_limit` is -1, this function will return all logs that belong
        to the result.
        """
        if logs_limit == -1:
            return self.logs
        else:
            return self.logs[:logs_limit]

# === BLOCK 2 (label=human, source_idx=line1621_human, name=check_columns_fit) ===
def check_columns_fit(unoccupied_columns, row, offset, row_length):
    """
    Checks if all the occupied columns in the row fit in the indices
    given by free columns.

    >>> check_columns_fit({0,1,2,3}, [(0, True), (2, True)], 0, 4)
    True
    >>> check_columns_fit({0,2,3}, [(2, True), (3, True)], 0, 4)
    True
    >>> check_columns_fit({}, [(2, True), (3, True)], 0, 4)
    False
    >>> check_columns_fit({0}, [(2, True)], 2, 4)
    True
    >>> check_columns_fit({0}, [(3, True)], 2, 4)
    False

    """
    for index, item in row:
        adjusted_index = (index + offset) % row_length

        # Check if the index is in the appropriate place.
        if adjusted_index not in unoccupied_columns:
            return False

    return True

# === BLOCK 3 (label=lm, source_idx=line4910_lm, name=add_agent) ===
def add_agent(self, overall_index=None, team_index=None):
        """
        Creates the agent using self.agent_class and adds it to the index manager.
        :param overall_index: The index of the bot in the config file if it already exists.
        :param team_index: The index of the team to place the agent in
        :return agent: an Agent (gui_agent) with either given index or a free one, returns None if there is no index given and all indices are occupied
        """
        agent = self.agent_class(self.game_state, self.index, overall_index, team_index)
        self.index_manager.add_agent(agent)
        return agent

# === BLOCK 4 (label=lm, source_idx=line2261_lm, name=_create_app) ===
def _create_app(self, color_depth, term='xterm'):
        """
        Create CommandLineInterface for this client.
        Called when the client wants to attach the UI to the server.
        """
        return CommandLineInterface(self, color_depth, term)

# === BLOCK 5 (label=human, source_idx=line431_human, name=reset_poller) ===
def reset_poller(poll=None):
    """replace the scheduler's poller, throwing away any pre-existing state

    this is only really a good idea in the new child process after a fork(2).
    """
    state.poller = poll or poller.best()
    log.info("resetting fd poller, using %s" % type(state.poller).__name__)

# === BLOCK 6 (label=human, source_idx=line1422_human, name=select_command) ===
def select_command(corrected_commands):
    """Returns:

     - the first command when confirmation disabled;
     - None when ctrl+c pressed;
     - selected command.

    :type corrected_commands: Iterable[thefuck.types.CorrectedCommand]
    :rtype: thefuck.types.CorrectedCommand | None

    """
    try:
        selector = CommandSelector(corrected_commands)
    except NoRuleMatched:
        logs.failed('No fucks given' if get_alias() == 'fuck'
                    else 'Nothing found')
        return

    if not settings.require_confirmation:
        logs.show_corrected_command(selector.value)
        return selector.value

    logs.confirm_text(selector.value)

    for action in read_actions():
        if action == const.ACTION_SELECT:
            sys.stderr.write('\n')
            return selector.value
        elif action == const.ACTION_ABORT:
            logs.failed('\nAborted')
            return
        elif action == const.ACTION_PREVIOUS:
            selector.previous()
            logs.confirm_text(selector.value)
        elif action == const.ACTION_NEXT:
            selector.next()
            logs.confirm_text(selector.value)
