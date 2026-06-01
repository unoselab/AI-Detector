# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line5253_human, name=run) ===
def run(self):
        """
        Actual run method that starts the processing of jobs and initiates the status polling, or
        performs job cancelling or cleaning, depending on the task parameters.
        """
        task = self.task
        self._outputs = self.output()

        # create the job dashboard interface
        self.dashboard = task.create_job_dashboard() or NoJobDashboard()

        # read submission data and reset some values
        submitted = not task.ignore_submission and self._outputs["submission"].exists()
        if submitted:
            self.submission_data.update(self._outputs["submission"].load(formatter="json"))
            task.tasks_per_job = self.submission_data.tasks_per_job
            self.dashboard.apply_config(self.submission_data.dashboard_config)

        # when the branch outputs, i.e. the "collection" exists, just create dummy control outputs
        if "collection" in self._outputs and self._outputs["collection"].exists():
            self.touch_control_outputs()

        # cancel jobs?
        elif self._cancel_jobs:
            if submitted:
                self.cancel()

        # cleanup jobs?
        elif self._cleanup_jobs:
            if submitted:
                self.cleanup()

        # submit and/or wait while polling
        else:
            # maybe set a tracking url
            tracking_url = self.dashboard.create_tracking_url()
            if tracking_url:
                task.set_tracking_url(tracking_url)

            # ensure the output directory exists
            if not submitted:
                self._outputs["submission"].parent.touch()

            # at this point, when the status file exists, it is considered outdated
            if "status" in self._outputs:
                self._outputs["status"].remove()

            try:
                # instantiate the configured job file factory, not kwargs yet
                self.job_file_factory = self.create_job_file_factory()

                # submit
                if not submitted:
                    # set the initial list of unsubmitted jobs
                    branches = sorted(task.branch_map.keys())
                    branch_chunks = list(iter_chunks(branches, task.tasks_per_job))
                    self.submission_data.unsubmitted_jobs = OrderedDict(
                        (i + 1, branches) for i, branches in enumerate(branch_chunks)
                    )
                    self.submit()

                    # sleep once to give the job interface time to register the jobs
                    post_submit_delay = self._get_task_attribute("post_submit_delay")()
                    if post_submit_delay:
                        time.sleep(post_submit_delay)

                # start status polling when a) no_poll is not set, or b) the jobs were already
                # submitted so that failed jobs are resubmitted after a single polling iteration
                if not task.no_poll or submitted:
                    self.poll()

            finally:
                # in any event, cleanup the job file
                if self.job_file_factory:
                    self.job_file_factory.cleanup_dir(force=False)

# === BLOCK 2 (label=lm, source_idx=line3087_lm, name=build_conda_packages) ===
def build_conda_packages(self):
        """
        Run the Linux build and use converter to build OSX
        """
        self.build_linux()
        self.build_osx()

# === BLOCK 3 (label=lm, source_idx=line4588_lm, name=pull_request) ===
def pull_request(self, file):
        """ Create a pull request

        :param file: File to push through pull request
        :return: URL of the PullRequest or Proxy Error
        """
        try:
            return self.github.create_pull(
                title=self.title,
                body=self.body,
                head=self.head,
                base=self.base,
                maintainer_can_modify=True,
                repo=self.repo,
                file=file
            )
        except Exception as e:
            return e

# === BLOCK 4 (label=lm, source_idx=line5233_lm, name=get_auth) ===
def get_auth(sock, dname, protocol, host, dno):
    """auth_name, auth_data = get_auth(sock, dname, protocol, host, dno)

    Return authentication data for the display on the other side of
    SOCK, which was opened with DNAME, HOST and DNO, using PROTOCOL.

    Return AUTH_NAME and AUTH_DATA, two strings to be used in the
    connection setup request.
    """
    # Get the authentication data from the other side.
    sock.send(b'AUTH\n')
    auth_name = sock.recv(1024).decode('utf-8').strip()
    auth_data = sock.recv(1024).decode('utf-8').strip()
    return auth_name, auth_data

# === BLOCK 5 (label=human, source_idx=line4550_human, name=_on_namreply) ===
def _on_namreply(self, connection, event):
        """
        event.arguments[0] == "@" for secret channels,
                          "*" for private channels,
                          "=" for others (public channels)
        event.arguments[1] == channel
        event.arguments[2] == nick list
        """

        ch_type, channel, nick_list = event.arguments

        if channel == '*':
            # User is not in any visible channel
            # http://tools.ietf.org/html/rfc2812#section-3.2.5
            return

        for nick in nick_list.split():
            nick_modes = []

            if nick[0] in self.connection.features.prefix:
                nick_modes.append(self.connection.features.prefix[nick[0]])
                nick = nick[1:]

            for mode in nick_modes:
                self.channels[channel].set_mode(mode, nick)

            self.channels[channel].add_user(nick)

# === BLOCK 6 (label=human, source_idx=line2600_human, name=notification_message) ===
def notification_message(cls, item):
        """Convert an RPCRequest item to a message."""
        assert isinstance(item, Notification)
        return cls.encode_payload(cls.request_payload(item, None))
