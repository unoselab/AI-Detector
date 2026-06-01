# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line6490_human, name=request_session) ===
def request_session(token, url=None):
	"""
	Requests a WebSocket session for the Real-Time Messaging API.

	Returns a SessionMetadata object containing the information retrieved from
	the API call.
	"""
	if url is None:
		api = SlackApi()
	else:
		api = SlackApi(url)

	response = api.rtm.start(token=token)
	return SessionMetadata(response, api, token)

# === BLOCK 2 (label=lm, source_idx=line1145_lm, name=_build_state) ===
async def _build_state(self,
                           request: Request,
                           message: BaseMessage,
                           responder: Responder) \
            -> Tuple[
                Optional[BaseState],
                Optional[BaseTrigger],
                Optional[bool],
            ]:
        """
        Build the state for this request.
        """
        state = None
        trigger = None
        is_new = False

        if message.state:
            state = await self._load_state(message.state)
            if state:
                trigger = await self._load_trigger(state.trigger)
                if trigger:
                    is_new = False
                else:
                    state = None

        if not state:
            state = await self._build_state_from_request(request, message)
            if state:
                is_new = True

        if not state:
            state = await self._build_state_from_message(message)
            if state:
                is_new = True

        if not state:
            state = await self._build_state_from_responder(responder)
            if state:
                is_new = True

        if not state:
            state = await self._build_state_from_default()
            if state:
                is_new = True

        return state, trigger, is_new

# === BLOCK 3 (label=lm, source_idx=line2384_lm, name=process_result_value) ===
def process_result_value(self, value: Optional[str],
                             dialect: Dialect) -> List[int]:
        """Convert things on the way from the database to Python."""
        if value is None:
            return []
        return [int(x) for x in value.split(',')]

# === BLOCK 4 (label=human, source_idx=line6357_human, name=coreSSH) ===
def coreSSH(self, *args, **kwargs):
        """
        If strict=False, strict host key checking will be temporarily disabled.
        This is provided as a convenience for internal/automated functions and
        ought to be set to True whenever feasible, or whenever the user is directly
        interacting with a resource (e.g. rsync-cluster or ssh-cluster). Assumed
        to be False by default.

        kwargs: input, tty, appliance, collectStdout, sshOptions, strict
        """
        commandTokens = ['ssh', '-t']
        strict = kwargs.pop('strict', False)
        if not strict:
            kwargs['sshOptions'] = ['-oUserKnownHostsFile=/dev/null', '-oStrictHostKeyChecking=no'] \
                                 + kwargs.get('sshOptions', [])
        sshOptions = kwargs.pop('sshOptions', None)
        # Forward ports:
        # 3000 for Grafana dashboard
        # 9090 for Prometheus dashboard
        # 5050 for Mesos dashboard (although to talk to agents you will need a proxy)
        commandTokens.extend(['-L', '3000:localhost:3000', \
                              '-L', '9090:localhost:9090', \
                              '-L', '5050:localhost:5050'])
        if sshOptions:
            # add specified options to ssh command
            assert isinstance(sshOptions, list)
            commandTokens.extend(sshOptions)
        # specify host
        user = kwargs.pop('user', 'core')   # CHANGED: Is this needed?
        commandTokens.append('%s@%s' % (user,str(self.effectiveIP)))
        appliance = kwargs.pop('appliance', None)
        if appliance:
            # run the args in the appliance
            tty = kwargs.pop('tty', None)
            ttyFlag = '-t' if tty else ''
            commandTokens += ['docker', 'exec', '-i', ttyFlag, 'toil_leader']

        inputString = kwargs.pop('input', None)
        if inputString is not None:
            kwargs['stdin'] = subprocess.PIPE
        collectStdout = kwargs.pop('collectStdout', None)
        if collectStdout:
            kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE

        logger.debug('Node %s: %s', self.effectiveIP, ' '.join(args))
        args = list(map(pipes.quote, args))
        commandTokens += args
        logger.debug('Full command %s', ' '.join(commandTokens))
        popen = subprocess.Popen(commandTokens, **kwargs)
        stdout, stderr = popen.communicate(input=inputString)
        # at this point the process has already exited, no need for a timeout
        resultValue = popen.wait()
        # ssh has been throwing random 255 errors - why?
        if resultValue != 0:
            logger.debug('SSH Error (%s) %s' % (resultValue, stderr))
            raise RuntimeError('Executing the command "%s" on the appliance returned a non-zero '
                               'exit code %s with stdout %s and stderr %s'
                               % (' '.join(args), resultValue, stdout, stderr))
        return stdout

# === BLOCK 5 (label=human, source_idx=line5121_human, name=connect_ws) ===
def connect_ws(self, path: str) -> _WSRequestContextManager:
        """
        Connect to a websocket in order to use API parameters

        In reality, aiohttp.session.ws_connect returns a aiohttp.client._WSRequestContextManager instance.
        It must be used in a with statement to get the ClientWebSocketResponse instance from it (__aenter__).
        At the end of the with statement, aiohttp.client._WSRequestContextManager.__aexit__ is called
        and close the ClientWebSocketResponse in it.

        :param path: the url path
        :return:
        """
        url = self.reverse_url(self.connection_handler.ws_scheme, path)
        return self.connection_handler.session.ws_connect(url, proxy=self.connection_handler.proxy)

# === BLOCK 6 (label=lm, source_idx=line1852_lm, name=change_approver_email_address) ===
def change_approver_email_address(self, order_id, approver_email):
        """Change the approver email address for an ordered SSL certificate."""
        self.api.change_approver_email_address(order_id, approver_email)
