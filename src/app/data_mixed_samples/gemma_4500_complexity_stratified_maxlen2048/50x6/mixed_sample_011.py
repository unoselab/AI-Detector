# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line5086_human, name=not_user_filter) ===
def not_user_filter(config, message, fasnick=None, *args, **kw):
    """ Everything except a particular user

    Use this rule to exclude messages that are associated with one or more
    users. Specify several users by separating them with a comma ','.
    """

    fasnick = kw.get('fasnick', fasnick)
    if not fasnick:
        return False

    fasnick = (fasnick or []) and fasnick.split(',')
    valid = True
    for nick in fasnick:
        if nick.strip() in fmn.rules.utils.msg2usernames(message, **config):
            valid = False
            break

    return valid

# === BLOCK 2 (label=lm, source_idx=line2401_lm, name=max_bit_rate) ===
def max_bit_rate(self):
        """
        Returns a tuple with the maximun upstream- and downstream-rate
        of the given connection. The rate is given in bits/sec.
        """
        return self.upstream_rate, self.downstream_rate

# === BLOCK 3 (label=lm, source_idx=line2440_lm, name=create_groups) ===
def create_groups(iam_client, groups):
    """
    Create a number of IAM group, silently handling exceptions when entity already exists
                                        .
    :param iam_client:                  AWS API client for IAM
    :param groups:                      Name of IAM groups to be created.

    :return:                            None
    """
    try:
        iam_client.create_group(GroupName=group_name)
    except iam_client.exceptions.EntityAlreadyExistsException:
        pass

# === BLOCK 4 (label=human, source_idx=line5641_human, name=pair_list) ===
def pair_list(args):
    """ List pairs within a container. """

    # Case 1: retrieve pairs within a named data entity
    if args.entity_type and args.entity:
        # Edge case: caller asked for pair within a pair (itself)
        if args.entity_type == 'pair':
            return [ args.entity.strip() ]
        # Edge case: pairs for a participant, which has to be done hard way
        # by iteratiing over all samples (see firecloud/discussion/9648)
        elif args.entity_type == 'participant':
            entities = _entity_paginator(args.project, args.workspace,
                                     'pair', page_size=2000)
            return [ e['name'] for e in entities if
                     e['attributes']['participant']['entityName'] == args.entity]

        # Otherwise retrieve the container entity
        r = fapi.get_entity(args.project, args.workspace, args.entity_type, args.entity)
        fapi._check_response_code(r, 200)
        pairs = r.json()['attributes']["pairs"]['items']
        return [ pair['entityName'] for pair in pairs]

    # Case 2: retrieve all pairs within a workspace
    return __get_entities(args, "pair", page_size=2000)

# === BLOCK 5 (label=lm, source_idx=line3690_lm, name=HandleWellKnownFlows) ===
def HandleWellKnownFlows(self, messages):
    """Hands off messages to well known flows."""
    for message in messages:
        flow_name = message.get('flow')
        if flow_name in self.well_known_flows:
            self.well_known_flows[flow_name].handle(message)

# === BLOCK 6 (label=human, source_idx=line7258_human, name=sample_bad_readout) ===
def sample_bad_readout(program, num_samples, assignment_probs, cxn):
    """
    Generate `n` samples of measuring all outcomes of a Quil `program`
    assuming the assignment probabilities `assignment_probs` by simulating the
    wave function on a qvm QVMConnection `cxn`

    :param pyquil.quil.Program program: The program.
    :param int num_samples: The number of samples
    :param numpy.ndarray assignment_probs: A matrix of assignment probabilities
    :param QVMConnection cxn: the QVM connection.
    :return: The resulting sampled outcomes from assignment_probs applied to cxn, one dimensional.
    :rtype: numpy.ndarray
    """
    wf = cxn.wavefunction(program)
    return sample_outcomes(assignment_probs.dot(abs(wf.amplitudes.ravel())**2), num_samples)
