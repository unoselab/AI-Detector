# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line455_lm, name=delist) ===
def delist(values):
    """Reduce lists of zero or one elements to individual values."""
    if not isinstance(values, list):
        raise TypeError("Input must be a list.")
    if len(values) == 0:
        raise ValueError("Input list cannot be empty.")
    if len(values) > 1:
        raise ValueError("Input list must have zero or one elements.")
    return values[0]

# === BLOCK 2 (label=lm, source_idx=line926_lm, name=_getPlotData) ===
def _getPlotData(self):
        """ Turns the resultsByClass Dict into a list of bin groups skipping the uncertain group if empty

        return: (label list, ydata list)
        :rtype: tuple(list(str), list(float))
        """
        label = []
        ydata = []
        for key, value in self.resultsByClass.items():
            if key!= "Uncertain":
                label.append(key)
                ydata.append(value)
        return label, ydata

# === BLOCK 3 (label=human, source_idx=line951_human, name=flag) ===
def flag(self, payload):
        """Set a single flag on a resource.

        :param payload:
            t: can be one of make_public, make_private, make_shareable,
            make_not_shareable, make_discoverable, make_not_discoverable
        :return:
            empty but with 202 status_code
        """
        url = "{url_base}/resource/{pid}/flag/".format(url_base=self.hs.url_base,
                                                       pid=self.pid)

        r = self.hs._request('POST', url, None, payload)
        return r

# === BLOCK 4 (label=human, source_idx=line1541_human, name=deployment_operations_list) ===
def deployment_operations_list(name, resource_group, result_limit=10, **kwargs):
    """
    .. versionadded:: 2019.2.0

    List all deployment operations within a deployment.

    :param name: The name of the deployment to query.

    :param resource_group: The resource group name assigned to the
        deployment.

    :param result_limit: (Default: 10) The limit on the list of deployment
        operations.

    CLI Example:

    .. code-block:: bash

        salt-call azurearm_resource.deployment_operations_list testdeploy testgroup

    """
    result = {}
    resconn = __utils__['azurearm.get_client']('resource', **kwargs)
    try:
        operations = __utils__['azurearm.paged_object_to_list'](
            resconn.deployment_operations.list(
                resource_group_name=resource_group,
                deployment_name=name,
                top=result_limit
            )
        )

        for oper in operations:
            result[oper['operation_id']] = oper
    except CloudError as exc:
        __utils__['azurearm.log_cloud_error']('resource', str(exc), **kwargs)
        result = {'error': str(exc)}

    return result

# === BLOCK 5 (label=lm, source_idx=line1755_lm, name=dframe) ===
def dframe(self):
        """
        Deprecated method to convert a MultiDimensionalMapping to
        a pandas DataFrame. Conversion to a dataframe now only
        supported by specific subclasses such as UniformNdMapping
        types.
        """
        raise TypeError("dframe is not supported for this type of MultiDimensionalMapping")

# === BLOCK 6 (label=human, source_idx=line200_human, name=server_inspect_exception) ===
def server_inspect_exception(self, req_event, rep_event, task_ctx, exc_info):
        """
        Called when an exception has been raised in the code run by ZeroRPC
        """
        # Hide the zerorpc internal frames for readability, for a REQ/REP or
        # REQ/STREAM server the frames to hide are:
        # - core.ServerBase._async_task
        # - core.Pattern*.process_call
        # - core.DecoratorBase.__call__
        #
        # For a PUSH/PULL or PUB/SUB server the frame to hide is:
        # - core.Puller._receiver
        if self._hide_zerorpc_frames:
            traceback = exc_info[2]
            while traceback:
                zerorpc_frame = traceback.tb_frame
                zerorpc_frame.f_locals['__traceback_hide__'] = True
                frame_info = inspect.getframeinfo(zerorpc_frame)
                # Is there a better way than this (or looking up the filenames
                # or hardcoding the number of frames to skip) to know when we
                # are out of zerorpc?
                if frame_info.function == '__call__' \
                        or frame_info.function == '_receiver':
                    break
                traceback = traceback.tb_next

        self._sentry_client.captureException(
            exc_info,
            extra=task_ctx
        )
