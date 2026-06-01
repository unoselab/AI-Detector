# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line4438_lm, name=score) ===
def score(self, X, y=None):
        """Compute the log probability under the model.

        Parameters
        ----------
        X : array_like, shape (n_samples, n_features)
            List of n_features-dimensional data points.  Each row
            corresponds to a single data point.

        Returns
        -------
        logprob : array_like, shape (n_samples,)
            Log probabilities of each data point in X
        """
        import numpy as np
        X = np.asarray(X)
        n_samples, n_features = X.shape

        # Assuming the model has attributes self.means_ and self.covs_
        # (or a shared self.cov_) as per standard Gaussian Mixture/Distribution models
        if hasattr(self, 'covs_') and self.covs_.ndim == 3:
            # Case: Individual covariance matrices per component/sample
            # This is a simplified implementation for a single Gaussian
            # If this is a GMM, the logic would involve summing over components
            pass

        # Standard implementation for a single Multivariate Normal distribution
        # log p(x) = -0.5 * [ (x-mu)^T * Sigma^-1 * (x-mu) + log|Sigma| + k*log(2pi) ]
        diff = X - self.means_
        inv_cov = np.linalg.inv(self.covs_)
        log_det = np.linalg.slogdet(self.covs_)[1]

        # Quadratic form: (x-mu)^T * Sigma^-1 * (x-mu)
        quad_form = np.sum(diff @ inv_cov * diff, axis=1)

        logprob = -0.5 * (quad_form + log_det + n_features * np.log(2 * np.pi))
        return logprob

# === BLOCK 2 (label=human, source_idx=line3905_human, name=title_has_tag) ===
def title_has_tag(page, lang, tag):
    """
    Check if a Title object is associated with the given tag.
    This function does not use fallbacks to retrieve title object.

    :param page: a Page instance
    :param lang: a language code
    :param tag: a Tag instance or a slug string.

    :return: whether the Title instance has the given tag attached (False if no Title or no
             attached TitleTags exists)
    :type: Boolean
    """
    from .models import TitleTags
    if hasattr(tag, 'slug'):
        slug = tag.slug
    else:
        slug = tag
    try:
        return page.get_title_obj(
            language=lang, fallback=False
        ).titletags.tags.filter(slug=slug).exists()
    except TitleTags.DoesNotExist:
        return False

# === BLOCK 3 (label=lm, source_idx=line6120_lm, name=get_nested_group_users) ===
def get_nested_group_users(self, groupname):
        """Retrieves a list of all users that directly or indirectly belong to the given groupname.

        Args:
            groupname: The group name.


        Returns:
            list:
                A list of strings of user names.
        """
        users = set()
        groups_to_process = [groupname]
        processed_groups = set()

        while groups_to_process:
            current_group = groups_to_process.pop()
            if current_group in processed_groups:
                continue

            processed_groups.add(current_group)

            # Assuming self has methods to get members and subgroups
            # Adjust method names based on the actual API implementation
            members = self.get_group_members(current_group)
            subgroups = self.get_group_subgroups(current_group)

            for member in members:
                if self.is_user(member):
                    users.add(member)
                else:
                    groups_to_process.append(member)

            for subgroup in subgroups:
                groups_to_process.append(subgroup)

        return list(users)

# === BLOCK 4 (label=human, source_idx=line1926_human, name=mount) ===
def mount(self,
              fstype=None,
              options=None,
              auth_no_user_interaction=None):
        """Mount filesystem."""
        return self._M.Filesystem.Mount(
            '(a{sv})',
            filter_opt({
                'fstype': ('s', fstype),
                'options': ('s', ','.join(options or [])),
                'auth.no_user_interaction': ('b', auth_no_user_interaction),
            })
        )

# === BLOCK 5 (label=human, source_idx=line5402_human, name=disconnect_all_containers_from_network) ===
def disconnect_all_containers_from_network(network_id):
    """
    .. versionadded:: 2018.3.0

    Runs :py:func:`docker.disconnect_container_from_network
    <salt.modules.dockermod.disconnect_container_from_network>` on all
    containers connected to the specified network, and returns the names of all
    containers that were disconnected.

    network_id
        Network name or ID

    CLI Examples:

    .. code-block:: bash

        salt myminion docker.disconnect_all_containers_from_network mynet
        salt myminion docker.disconnect_all_containers_from_network 1f9d2454d0872b68dd9e8744c6e7a4c66b86f10abaccc21e14f7f014f729b2bc
    """
    connected_containers = connected(network_id)
    ret = []
    failed = []
    for cname in connected_containers:
        try:
            disconnect_container_from_network(cname, network_id)
            ret.append(cname)
        except CommandExecutionError as exc:
            msg = exc.__str__()
            if '404' not in msg:
                # If 404 was in the error, then the container no longer exists,
                # so to avoid a race condition we won't consider 404 errors to
                # men that removal failed.
                failed.append(msg)
    if failed:
        raise CommandExecutionError(
            'One or more containers failed to be removed',
            info={'removed': ret, 'errors': failed}
        )
    return ret

# === BLOCK 6 (label=lm, source_idx=line3018_lm, name=remove_categories) ===
def remove_categories(self, categories, ignore_absences=False):
        """
        Non destructive category removal.

        Parameters
        ----------
        categories : list
            list of categories to remove
        ignore_absences : bool, False by default
            if categories does not appear, don't raise an error, just move on.

        Returns
        -------
        TermDocMatrix, new object with categories removed.
        """
        import copy
        new_obj = copy.deepcopy(self)
        for cat in categories:
            if cat not in self.categories:
                if not ignore_absences:
                    raise KeyError(f"Category {cat} not found in matrix.")
                continue

            idx = self.categories.index(cat)
            new_obj.categories.pop(idx)
            # Assuming the matrix data is stored in an attribute like 'matrix' or 'data'
            # and needs to be sliced to remove the corresponding row/column.
            # Since the internal structure isn't specified, we handle the category list.
            # If the object manages a numpy array or similar, it would be sliced here.
            if hasattr(new_obj, 'matrix'):
                import numpy as np
                new_obj.matrix = np.delete(new_obj.matrix, idx, axis=0)

        return new_obj
