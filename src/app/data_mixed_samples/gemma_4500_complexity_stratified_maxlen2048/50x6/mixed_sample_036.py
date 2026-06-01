# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3481_human, name=config_profile_list) ===
def config_profile_list(self):
        """Return config profile list from DCNM."""

        these_profiles = self._config_profile_list() or []
        profile_list = [q for p in these_profiles for q in
                        [p.get('profileName')]]
        return profile_list

# === BLOCK 2 (label=lm, source_idx=line4369_lm, name=_role_present) ===
def _role_present(ret, IdentityPoolId, AuthenticatedRole, UnauthenticatedRole, conn_params):
    """
    Helper function to set the Roles to the identity pool
    """
    if AuthenticatedRole:
        ret['AuthenticatedRoleArn'] = AuthenticatedRole
    if UnauthenticatedRole:
        ret['RoleArn'] = UnauthenticatedRole
    return ret

# === BLOCK 3 (label=human, source_idx=line8127_human, name=_parametersAsIndex) ===
def _parametersAsIndex( self, ps ):
        """Private method to turn a parameter dict into a string suitable for
        keying a dict.

        ps: the parameters as a hash
        returns: a string key"""
        k = ""
        for p in sorted(ps.keys()):       # normalise the parameters
            v = ps[p]
            k = k + "{p}=[[{v}]];".format(p = p, v = v)
        return k

# === BLOCK 4 (label=human, source_idx=line5288_human, name=l2norm_squared) ===
def l2norm_squared(a):
    """
    L2 normalize squared
    """
    value = 0
    for i in xrange(a.shape[1]):
        value += np.dot(a[:,i],a[:,i])
    return value

# === BLOCK 5 (label=lm, source_idx=line3819_lm, name=rotMatrix2AxisAndAngle) ===
def rotMatrix2AxisAndAngle(R):
    """
    stackoverflow.com/questions/12463487/obtain-rotation-axis-from-rotation-matrix-and-translation-vector-in-opencv

    R : 3x3 rotation matrix
    returns axis, angle

    """
    import numpy as np
    angle = np.arccos(np.clip((np.trace(R) - 1.0) / 2.0, -1.0, 1.0))
    if angle < 1e-6:
        return np.array([0.0, 0.0, 1.0]), angle
    elif angle > np.pi - 1e-6:
        # Special case for 180 degrees
        # Find the column of R + I with the largest norm
        mat = R + np.eye(3)
        axis = mat[:, np.argmax(np.linalg.norm(mat, axis=0))]
    else:
        # General case
        x = R[2, 1] - R[1, 2]
        y = R[0, 2] - R[2, 0]
        z = R[1, 0] - R[0, 1]
        axis = np.array([x, y, z])

    axis = axis / np.linalg.norm(axis)
    return axis, angle

# === BLOCK 6 (label=lm, source_idx=line8616_lm, name=wallinterzone) ===
def wallinterzone(idf, bsdobject, deletebsd=True, setto000=False):
    """return an wall:interzone object if the bsd (buildingsurface:detailed) 
    is an interaone wall"""
    if bsdobject.ObjectType.lower() == 'buildingsurface:detailed':
        if 'interzone' in bsdobject.Name.lower():
            if deletebsd:
                idf.remove(bsdobject)

            wall_interzone = idf.new_wallinterzone()
            wall_interzone.Name = bsdobject.Name

            if setto000:
                wall_interzone.OutsideFaceTemperature = 0.0
                wall_interzone.InsideFaceTemperature = 0.0

            return wall_interzone
    return None
