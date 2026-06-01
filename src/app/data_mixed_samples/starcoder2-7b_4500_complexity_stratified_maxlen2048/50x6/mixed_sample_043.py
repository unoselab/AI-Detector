# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6553_lm, name=options) ===
def options(self, url, **kwargs):
        r"""Sends a OPTIONS request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """
        return self.request('OPTIONS', url, **kwargs)

# === BLOCK 2 (label=lm, source_idx=line6177_lm, name=_xml_pretty_print) ===
def _xml_pretty_print(self, data):
        """Pretty print xml data
        """
        return xml.dom.minidom.parseString(data).toprettyxml(indent="  ")

# === BLOCK 3 (label=human, source_idx=line3782_human, name=get_field_type) ===
def get_field_type(f):
    """Obtain the type name of a GRPC Message field."""
    types = (t[5:] for t in dir(f) if t[:4] == 'TYPE' and
             getattr(f, t) == f.type)
    return next(types)

# === BLOCK 4 (label=lm, source_idx=line5220_lm, name=get_descriptions) ===
def get_descriptions(fastas):
    """
    get the description for each ORF 
    """
    descriptions = []
    for fasta in fastas:
        descriptions.append(fasta.description)
    return descriptions

# === BLOCK 5 (label=human, source_idx=line1707_human, name=add_forward_workflow) ===
def add_forward_workflow(self, dag, sections, satisfies=None):
        """Add a forward-workflow, return number of nodes added
        """
        dag.new_forward_workflow()

        if 'DAG' in env.config['SOS_DEBUG'] or 'ALL' in env.config['SOS_DEBUG']:
            env.log_to_file(
                'DAG', f'Adding mini-workflow with {len(sections)} sections')
        default_input: sos_targets = sos_targets([])
        for idx, section in enumerate(sections):
            #
            res = analyze_section(section, default_input=default_input)

            environ_vars = res['environ_vars']
            signature_vars = res['signature_vars']
            changed_vars = res['changed_vars']
            # parameters, if used in the step, should be considered environmental
            environ_vars |= env.parameter_vars & signature_vars

            # add shared to targets
            if res['changed_vars']:
                if 'provides' in section.options:
                    if isinstance(section.options['provides'], str):
                        section.options.set('provides',
                                            [section.options['provides']])
                else:
                    section.options.set('provides', [])
                #
                section.options.set(
                    'provides', section.options['provides'] +
                    [sos_variable(var) for var in changed_vars])

            context = {
                '__signature_vars__': signature_vars,
                '__environ_vars__': environ_vars,
                '__changed_vars__': changed_vars,
                '__dynamic_depends__': res['dynamic_depends'],
                '__dynamic_input__': res['dynamic_input']
            }

            # for nested workflow, the input is specified by sos_run, not None.
            if idx == 0:
                context['__step_output__'] = env.sos_dict['__step_output__']
            # can be the only step
            if idx == len(sections) - 1 and satisfies is not None:
                res['step_output'].extend(satisfies)

            dag.add_step(
                section.uuid,
                section.step_name(),
                idx,
                res['step_input'],
                res['step_depends'],
                res['step_output'],
                context=context)
            default_input = res['step_output']
        return len(sections)

# === BLOCK 6 (label=human, source_idx=line4517_human, name=now) ===
def now(self):
		"""
		Return a :py:class:`datetime.datetime` instance representing the current time.

		:rtype: :py:class:`datetime.datetime`
		"""
		if self.use_utc:
			return datetime.datetime.utcnow()
		else:
			return datetime.datetime.now()
