# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line8572_human, name=wait_until_page_ready) ===
def wait_until_page_ready(page_object, timeout=WTF_TIMEOUT_MANAGER.NORMAL):
        """Waits until document.readyState == Complete (e.g. ready to execute javascript commands)

        Args:
            page_object (PageObject) : PageObject class

        Kwargs:
            timeout (number) : timeout period
        """
        try:
            do_until(lambda: page_object.webdriver.execute_script("return document.readyState").lower()
                     == 'complete', timeout)
        except wait_utils.OperationTimeoutError:
            raise PageUtilOperationTimeoutError(
                "Timeout occurred while waiting for page to be ready.")

# === BLOCK 2 (label=lm, source_idx=line1517_lm, name=calculate_marginal_likelihoods) ===
def calculate_marginal_likelihoods(tree, feature, frequencies):
    """
    Calculates marginal likelihoods for each tree node
    by multiplying state frequencies with their bottom-up and top-down likelihoods.

    :param tree: ete3.Tree, the tree of interest
    :param feature: str, character for which the likelihood is calculated
    :param frequencies: numpy array of state frequencies
    :return: void, stores the node marginal likelihoods in the get_personalised_feature_name(feature, LH) feature.
    """
    from ete3 import Tree
    import numpy as np

    def get_personalised_feature_name(f, suffix):
        return f"{f}_{suffix}"

    lh_feature = get_personalised_feature_name(feature, "LH")

    # Bottom-up pass: Calculate partial likelihoods
    for node in tree.traverse("postorder"):
        if node.is_leaf():
            # Initialize likelihoods for leaves based on observed state
            state = node.get_personalised_feature(feature)
            lh = np.zeros(len(frequencies))
            if state is not None and state.isdigit():
                lh[int(state)] = 1.0
            else:
                lh[:] = 1.0 # Ambiguous or missing
            node.add_personalised_feature(lh_feature, lh)
        else:
            # Combine children likelihoods (simplified Felsenstein's)
            # In a real scenario, this would involve a transition matrix P
            # Here we assume the 'LH' stored is the conditional likelihood
            children_lh = [child.get_personalised_feature(lh_feature) for child in node.children]
            combined_lh = np.prod(children_lh, axis=0)
            node.add_personalised_feature(lh_feature, combined_lh)

    # Top-down pass: Calculate marginals by incorporating frequencies
    # For a simple marginal likelihood at node i: P(state | data) 
    # proportional to frequency[state] * conditional_likelihood[state]
    for node in tree.traverse("preorder"):
        cond_lh = node.get_personalised_feature(lh_feature)
        marginal = frequencies * cond_lh
        # Normalize to get probabilities
        sum_marginal = np.sum(marginal)
        if sum_marginal > 0:
            marginal /= sum_marginal
        node.add_personalised_feature(lh_feature, marginal)

# === BLOCK 3 (label=lm, source_idx=line1016_lm, name=importSignedCertificate) ===
def importSignedCertificate(self, alias, certFile):
        """
        This operation imports a certificate authority (CA) signed SSL
        certificate into the key store.
        """
        with open(certFile, 'rb') as f:
            cert_data = f.read()
        self.keystore.import_certificate(alias, cert_data)

# === BLOCK 4 (label=lm, source_idx=line532_lm, name=console_check_for_keypress) ===
def console_check_for_keypress(flags: int = KEY_RELEASED) -> Key:
    """
    .. deprecated:: 9.3
        Use the :any:`tcod.event.get` function to check for events.
    """
    import tcod.console
    return tcod.console.check_for_keypress(flags)

# === BLOCK 5 (label=human, source_idx=line4369_human, name=_role_present) ===
def _role_present(ret, IdentityPoolId, AuthenticatedRole, UnauthenticatedRole, conn_params):
    """
    Helper function to set the Roles to the identity pool
    """
    r = __salt__['boto_cognitoidentity.get_identity_pool_roles'](IdentityPoolName='',
                                                                 IdentityPoolId=IdentityPoolId,
                                                                 **conn_params)
    if r.get('error'):
        ret['result'] = False
        failure_comment = ('Failed to get existing identity pool roles: '
                           '{0}'.format(r['error'].get('message', r['error'])))
        ret['comment'] = '{0}\n{1}'.format(ret['comment'], failure_comment)
        return

    existing_identity_pool_role = r.get('identity_pool_roles')[0].get('Roles', {})
    r = __salt__['boto_cognitoidentity.set_identity_pool_roles'](IdentityPoolId=IdentityPoolId,
                                                                 AuthenticatedRole=AuthenticatedRole,
                                                                 UnauthenticatedRole=UnauthenticatedRole,
                                                                 **conn_params)
    if not r.get('set'):
        ret['result'] = False
        failure_comment = ('Failed to set roles: '
                           '{0}'.format(r['error'].get('message', r['error'])))
        ret['comment'] = '{0}\n{1}'.format(ret['comment'], failure_comment)
        return

    updated_identity_pool_role = r.get('roles')

    if existing_identity_pool_role != updated_identity_pool_role:
        if not ret['changes']:
            ret['changes']['old'] = dict()
            ret['changes']['new'] = dict()
        ret['changes']['old']['Roles'] = existing_identity_pool_role
        ret['changes']['new']['Roles'] = r.get('roles')
        ret['comment'] = ('{0}\n{1}'.format(ret['comment'], 'identity pool roles updated.'))
    else:
        ret['comment'] = ('{0}\n{1}'.format(ret['comment'], 'identity pool roles is already current.'))

    return

# === BLOCK 6 (label=human, source_idx=line6051_human, name=is_marginable) ===
def is_marginable(self):
        """True if adding counts across this dimension axis is meaningful."""
        return self.dimension_type not in {DT.CA, DT.MR, DT.MR_CAT, DT.LOGICAL}
