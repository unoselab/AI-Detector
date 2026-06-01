# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line5174_lm, name=get_valid_task_types) ===
def get_valid_task_types():
    """Get the valid task types, e.g. signing.

    No longer a constant, due to code ordering issues.

    Returns:
        frozendict: maps the valid task types (e.g., signing) to their validation functions.

    """
    from frozendict import frozendict
    from . import task_validators
    return frozendict({
        "signing": task_validators.validate_signing,
        "encryption": task_validators.validate_encryption,
        "verification": task_validators.validate_verification,
    })

# === BLOCK 2 (label=human, source_idx=line6168_human, name=remove_video_for_course) ===
def remove_video_for_course(course_id, edx_video_id):
    """
    Soft deletes video for particular course.

    Arguments:
        course_id (str): id of the course
        edx_video_id (str): id of the video to be hidden
    """
    course_video = CourseVideo.objects.get(course_id=course_id, video__edx_video_id=edx_video_id)
    course_video.is_hidden = True
    course_video.save()

# === BLOCK 3 (label=lm, source_idx=line1581_lm, name=query) ===
def query(self, *args, **kwargs):
        """
        This method retrieve an iterable object that implements the method
        __iter__. The arguments given will compose the parameters in the
        request url.

        This method can be used compounded and recursively with query, filter,
        order, sort and facet methods.

        args: strings (String)

        kwargs: valid FIELDS_QUERY arguments.

        return: iterable object of Works metadata

        Example:
            >>> from crossref.restful import Works
            >>> works = Works()
            >>> query = works.query('Zika Virus')
            >>> query.url
            'https://api.crossref.org/works?query=Zika+Virus'
            >>> for item in query:
            ...     print(item['title'])
            ...
            ['Zika Virus']
            ['Zika virus disease']
            ['Zika Virus: Laboratory Diagnosis']
            ['Spread of Zika virus disease']
            ['Carditis in Zika Virus Infection']
            ['Understanding Zika virus']
            ['Zika Virus: History and Infectology']
            ...
        """
        params = kwargs.copy()
        if args:
            params['query'] = ' '.join(args)
        return self.filter(**params)

# === BLOCK 4 (label=lm, source_idx=line5769_lm, name=spawn) ===
async def spawn(self, agent_cls, *args, addr=None, **kwargs):
        """Spawn a new agent in a slave environment.

        :param str agent_cls:
            `qualname`` of the agent class.
            That is, the name should be in the form ``pkg.mod:cls``, e.g.
            ``creamas.core.agent:CreativeAgent``.
        :param str addr:
            Optional. Address for the slave enviroment's manager.
            If :attr:`addr` is None, spawns the agent in the slave environment
            with currently smallest number of agents.

        :returns: :class:`aiomas.rpc.Proxy` and address for the created agent.

        The ``*args`` and ``**kwargs`` are passed down to the agent's
        :meth:`__init__`.

        .. note::

            Use :meth:`~creamas.mp.MultiEnvironment.spawn_n` to spawn large
            number of agents with identical initialization parameters.
        """
        addr = await self.get_least_loaded_slave_addr()

        proxy, agent_addr = await self.manager.spawn_agent(
        addr, agent_cls, *args, **kwargs
        )
        return proxy, agent_addr

# === BLOCK 5 (label=human, source_idx=line2645_human, name=get) ===
def get(identifier, namespace='cid', domain='compound', operation=None, output='JSON', searchtype=None, **kwargs):
    """Request wrapper that automatically handles async requests."""
    if (searchtype and searchtype != 'xref') or namespace in ['formula']:
        response = request(identifier, namespace, domain, None, 'JSON', searchtype, **kwargs).read()
        status = json.loads(response.decode())
        if 'Waiting' in status and 'ListKey' in status['Waiting']:
            identifier = status['Waiting']['ListKey']
            namespace = 'listkey'
            while 'Waiting' in status and 'ListKey' in status['Waiting']:
                time.sleep(2)
                response = request(identifier, namespace, domain, operation, 'JSON', **kwargs).read()
                status = json.loads(response.decode())
            if not output == 'JSON':
                response = request(identifier, namespace, domain, operation, output, searchtype, **kwargs).read()
    else:
        response = request(identifier, namespace, domain, operation, output, searchtype, **kwargs).read()
    return response

# === BLOCK 6 (label=human, source_idx=line1495_human, name=set_connection_type) ===
def set_connection_type(self, connection_type):
        """
        Sets the connection resource type, i.e the way in which the Clients
        connects to a PLC.

        :param connection_type: 1 for PG, 2 for OP, 3 to 10 for S7 Basic
        """
        result = self.library.Cli_SetConnectionType(self.pointer,
                                                    c_uint16(connection_type))
        if result != 0:
            raise Snap7Exception("The parameter was invalid")
