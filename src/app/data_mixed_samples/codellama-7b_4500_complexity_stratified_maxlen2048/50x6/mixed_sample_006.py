# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line4401_lm, name=pubsub_channels) ===
def pubsub_channels(self, pattern=None):
        """Lists the currently active channels."""
        if pattern is None:
            pattern = ''
        return self.execute_command('PUBSUB CHANNELS', pattern)

# === BLOCK 2 (label=human, source_idx=line8943_human, name=_apply_concretization_strategies) ===
def _apply_concretization_strategies(self, addr, strategies, action):
        """
        Applies concretization strategies on the address until one of them succeeds.
        """

        # we try all the strategies in order
        for s in strategies:
            # first, we trigger the SimInspect breakpoint and give it a chance to intervene
            e = addr
            self.state._inspect(
                'address_concretization', BP_BEFORE, address_concretization_strategy=s,
                address_concretization_action=action, address_concretization_memory=self,
                address_concretization_expr=e, address_concretization_add_constraints=True
            )
            s = self.state._inspect_getattr('address_concretization_strategy', s)
            e = self.state._inspect_getattr('address_concretization_expr', addr)

            # if the breakpoint None'd out the strategy, we skip it
            if s is None:
                continue

            # let's try to apply it!
            try:
                a = s.concretize(self, e)
            except SimUnsatError:
                a = None

            # trigger the AFTER breakpoint and give it a chance to intervene
            self.state._inspect(
                'address_concretization', BP_AFTER,
                address_concretization_result=a
            )
            a = self.state._inspect_getattr('address_concretization_result', a)

            # return the result if not None!
            if a is not None:
                return a

        # well, we tried
        raise SimMemoryAddressError(
            "Unable to concretize address for %s with the provided strategies." % action
        )

# === BLOCK 3 (label=lm, source_idx=line7019_lm, name=components) ===
def components(self, obj, fmt=None, comm=True, **kwargs):
        """
        Returns data and metadata dictionaries containing HTML and JS
        components to include render in app, notebook, or standalone
        document. Depending on the backend the fmt defines the format
        embedded in the HTML, e.g. png or svg. If comm is enabled the
        JS code will set up a Websocket comm channel using the
        currently defined CommManager.
        """
        if fmt is None:
            fmt = self.fmt
        if fmt not in self.components:
            self.components[fmt] = {}
        if comm is True:
            comm = self.comm
        if comm is not False:
            self.components[fmt]['comm'] = comm
        self.components[fmt]['data'] = self.get_data(obj, **kwargs)
        self.components[fmt]['metadata'] = self.get_metadata(obj, **kwargs)
        return self.components[fmt]

# === BLOCK 4 (label=human, source_idx=line6224_human, name=health_check) ===
def health_check(self):
        """Gets a single item to determine if Dynamo is functioning."""
        logger.debug('Health Check on Table: {namespace}'.format(
            namespace=self.namespace
        ))

        try:
            self.get_all()
            return True

        except ClientError as e:
            logger.exception(e)
            logger.error('Error encountered with Database. Assume unhealthy')
            return False

# === BLOCK 5 (label=human, source_idx=line3792_human, name=GET_namespace_num_names) ===
def GET_namespace_num_names(self, path_info, namespace_id):
        """
        Get the number of names in a namespace
        Reply the number on success
        Reply 404 if the namespace does not exist
        Reply 502 on failure to talk to the blockstack server
        """
        if not check_namespace(namespace_id):
            return self._reply_json({'error': 'Invalid namespace'}, status_code=400)

        blockstackd_url = get_blockstackd_url()
        name_count = blockstackd_client.get_num_names_in_namespace(namespace_id, hostport=blockstackd_url)
        if json_is_error(name_count):
            log.error("Failed to load namespace count for {}: {}".format(namespace_id, name_count['error']))
            return self._reply_json({'error': 'Failed to load namespace count: {}'.format(name_count['error'])}, status_code=404)

        self._reply_json({'names_count': name_count})

# === BLOCK 6 (label=lm, source_idx=line6874_lm, name=delete_user) ===
def delete_user(self, user_id):
        """Delete user specified user.

        :param str user_id: the ID of the user to delete (Required)
        :returns: void
        """
        return self.delete(
            '/users/{user_id}'.format(
                user_id=user_id
            ),
            expected_status_code=204
        )
