# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1656_lm, name=set_cognitive_process) ===
def set_cognitive_process(self, grade_id=None):
        """Sets the cognitive process.

        arg:    gradeId (osid.id.Id): the new cognitive process
        raise:  INVALID_ARGUMENT - gradeId is invalid
        raise:  NoAccess - gradeId cannot be modified
        raise:  NullArgument - gradeId is null
        compliance: mandatory - This method must be implemented.

        """
        if grade_id is None:
            raise NullArgument()
        if not isinstance(grade_id, Id):
            raise InvalidArgument()
        if not self._can_modify_grade_id():
            raise NoAccess()
        self._my_grade_id = grade_id

# === BLOCK 2 (label=human, source_idx=line2530_human, name=step) ===
def step(self, y, u, t, h):
		"""
		This is called by solve, but can be called by the user who wants to
		run through an integration with a control force.

		y - state at t
		u - control inputs at t
		t - time
		h - step size
		"""
		k1 = h * self.func(t, y, u)
		k2 = h * self.func(t + .5*h, y + .5*h*k1, u)
		k3 = h * self.func(t + .5*h, y + .5*h*k2, u)
		k4 = h * self.func(t + h, y + h*k3, u)
		return y + (k1 + 2*k2 + 2*k3 + k4) / 6.0

# === BLOCK 3 (label=human, source_idx=line637_human, name=add_service) ===
def add_service(protocol=None, service_address=None, scheduler='wlc'):
    """
    Add a virtual service.

    protocol
        The service protocol(only support tcp, udp and fwmark service).

    service_address
        The LVS service address.

    scheduler
        Algorithm for allocating TCP connections and UDP datagrams to real servers.


    CLI Example:

    .. code-block:: bash

        salt '*' lvs.add_service tcp 1.1.1.1:80 rr
    """

    cmd = '{0} -A {1}'.format(__detect_os(),
                              _build_cmd(protocol=protocol,
                                         service_address=service_address,
                                         scheduler=scheduler))
    out = __salt__['cmd.run_all'](cmd, python_shell=False)

    # A non-zero return code means fail
    if out['retcode']:
        ret = out['stderr'].strip()
    else:
        ret = True
    return ret

# === BLOCK 4 (label=lm, source_idx=line3168_lm, name=read_meta) ===
def read_meta(self, f):
        """Read the headers of a file in file format and place them in the
        self.meta dictionary.
        """
        with open(f, 'r') as file:
            for line in file:
                if line.startswith('##'):
                    key, value = line[2:].split('=')
                    self.meta[key] = value

# === BLOCK 5 (label=lm, source_idx=line2289_lm, name=delete_tag) ===
async def delete_tag(self, tag):
        """
        DELETE /api/tags/{tag}.{_format}

        Permanently remove one tag from every entry

        :param tag: string The Tag
        :return data related to the ext
        """
        for entry in self.entries:
            if tag in entry.tags:
                entry.tags.remove(tag)
        return {"message": f"Tag '{tag}' deleted from all entries"}

# === BLOCK 6 (label=human, source_idx=line155_human, name=repl) ===
def repl():
    """Runs an IPython repl with some context"""

    try:
        import IPython
    except:
        print("ERROR: IPython is not installed. Please install it to use the repl.", file=sys.stderr)
        raise

    IPython.embed(user_ns=dict(
        settings=oz.settings,
        actions=oz._actions,
        uimodules=oz._uimodules,
        routes=oz._routes,
    ))
