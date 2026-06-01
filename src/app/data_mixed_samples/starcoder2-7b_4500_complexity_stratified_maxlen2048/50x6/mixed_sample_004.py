# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line273_lm, name=save) ===
def save(self, **kwargs):
        """Override save method to catch handled errors and repackage them as 400 errors."""
        try:
            super().save(**kwargs)
        except ValidationError as e:
            raise ValidationError(e.message_dict)

# === BLOCK 2 (label=lm, source_idx=line3173_lm, name=render_dot) ===
def render_dot(self, code, options, format, prefix='graphviz'):
    # type: (nodes.NodeVisitor, unicode, Dict, unicode, unicode) -> Tuple[unicode, unicode]
    """Render graphviz code into a PNG or PDF output file."""
    if format == 'png':
        ext = 'png'
        cmd = 'dot'
    elif format == 'pdf':
        ext = 'pdf'
        cmd = 'dot'
    else:
        raise ValueError('Unknown format: %s' % format)
    filename = prefix + '.' + ext
    with open(filename, 'w') as f:
        f.write(code)
    cmd = [cmd, '-T', format, filename]
    try:
        output = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        raise ValueError('Error running %s: %s' % (cmd, e.output))
    return (filename, output)

# === BLOCK 3 (label=human, source_idx=line4163_human, name=check_argument_types) ===
def check_argument_types(cllable = None, call_args = None, clss = None, caller_level = 0):
    """Can be called from within a function or method to apply typechecking to
    the arguments that were passed in by the caller. Checking is applied w.r.t.
    type hints of the function or method hosting the call to check_argument_types.
    """
    return _check_caller_type(False, cllable, call_args, clss, caller_level+1)

# === BLOCK 4 (label=lm, source_idx=line2349_lm, name=draw_rivers_on_image) ===
def draw_rivers_on_image(world, target, factor=1):
    """Draw only the rivers, it expect the background to be in place
    """
    for river in world.rivers:
        river.draw_on_image(target, factor)

# === BLOCK 5 (label=human, source_idx=line6135_human, name=build_access_service) ===
def build_access_service(did, price, consume_endpoint, service_endpoint, timeout, template_id):
        """
        Build the access service.

        :param did: DID, str
        :param price: Asset price, int
        :param consume_endpoint: url of the service provider, str
        :param service_endpoint: identifier of the service inside the asset DDO, str
        :param timeout: amount of time in seconds before the agreement expires, int
        :param template_id: id of the template use to create the service, str
        :return: ServiceAgreement
        """
        # TODO fill all the possible mappings
        param_map = {
            '_documentId': did_to_id(did),
            '_amount': price,
            '_rewardAddress': Keeper.get_instance().escrow_reward_condition.address,
        }
        sla_template_path = get_sla_template_path()
        sla_template = ServiceAgreementTemplate.from_json_file(sla_template_path)
        sla_template.template_id = template_id
        conditions = sla_template.conditions[:]
        for cond in conditions:
            for param in cond.parameters:
                param.value = param_map.get(param.name, '')

            if cond.timeout > 0:
                cond.timeout = timeout

        sla_template.set_conditions(conditions)
        sa = ServiceAgreement(
            1,
            sla_template,
            consume_endpoint,
            service_endpoint,
            ServiceTypes.ASSET_ACCESS
        )
        sa.set_did(did)
        return sa

# === BLOCK 6 (label=human, source_idx=line3572_human, name=ls_) ===
def ls_(active=None, cache=True, path=None):
    """
    Return a list of the containers available on the minion

    path
        path to the container parent directory
        default: /var/lib/lxc (system)

        .. versionadded:: 2015.8.0

    active
        If ``True``, return only active (i.e. running) containers

        .. versionadded:: 2015.5.0

    CLI Example:

    .. code-block:: bash

        salt '*' lxc.ls
        salt '*' lxc.ls active=True
    """
    contextvar = 'lxc.ls{0}'.format(path)
    if active:
        contextvar += '.active'
    if cache and (contextvar in __context__):
        return __context__[contextvar]
    else:
        ret = []
        cmd = 'lxc-ls'
        if path:
            cmd += ' -P {0}'.format(pipes.quote(path))
        if active:
            cmd += ' --active'
        output = __salt__['cmd.run_stdout'](cmd, python_shell=False)
        for line in output.splitlines():
            ret.extend(line.split())
        __context__[contextvar] = ret
        return ret
