# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1458_lm, name=create_seq) ===
def create_seq(self, project):
        """Create and return a new sequence

        :param project: the project for the sequence
        :type deps: :class:`jukeboxcore.djadapter.models.Project`
        :returns: The created sequence or None
        :rtype: None | :class:`jukeboxcore.djadapter.models.Sequence`
        :raises: None
        """
        seq = Sequence()
        seq.project = project
        seq.save()
        return seq

# === BLOCK 2 (label=lm, source_idx=line2893_lm, name=V) ===
def V(self,*args,**kwargs):
        """
        NAME:

           V

        PURPOSE:

           return Heliocentric Galactic rectangular y-velocity (aka "V")

        INPUT:

           t - (optional) time at which to get V (can be Quantity)

           obs=[X,Y,Z,vx,vy,vz] - (optional) position and velocity of observer 
                         in the Galactocentric frame
                         (in kpc and km/s) (default=[8.0,0.,0.,0.,220.,0.]; entries can be Quantity)
                         OR Orbit object that corresponds to the orbit
                         of the observer
                         Y is ignored and always assumed to be zero

           ro= (Object-wide default) physical scale for distances to use to convert (can be Quantity)

           vo= (Object-wide default) physical scale for velocities to use to convert (can be Quantity)

        OUTPUT:

           V(t) in km/s

        HISTORY:

           2011-02-24 - Written - Bovy (NYU)

        """
        t = kwargs.get('t', None)
        obs = kwargs.get('obs', [8.0, 0.0, 0.0, 0.0, 220.0, 0.0])
        ro = kwargs.get('ro', None)
        vo = kwargs.get('vo', None)
        if isinstance(obs, list):
            obs = [float(o) for o in obs]
        elif isinstance(obs, Orbit):
            obs = obs.getOrbit()
        else:
            raise TypeError("obs must be a list or an Orbit object")
        if t is not None:
            t = float(t)
        if ro is not None:
            ro = float(ro)
        if vo is not None:
            vo = float(vo)
        return self._V(t, obs, ro, vo)

# === BLOCK 3 (label=human, source_idx=line288_human, name=loads) ===
def loads(content):
    """Loads variable definitions from a string."""
    lines = _group_lines(line for line in content.split('\n'))
    lines = [
        (i, _parse_envfile_line(line))
        for i, line in lines if line.strip()
    ]
    errors = []
    # Reject files with duplicate variables (no sane default).
    duplicates = _find_duplicates(((i, line[0]) for i, line in lines))
    for i, variable, j in duplicates:
        errors.append(''.join([
                'Line %d: duplicate environment variable "%s": ',
                'already appears on line %d.',
            ]) % (i + 1, variable, j + 1)
        )
    # Done!
    if errors:
        raise ValueError(errors)
    return {k: v for _, (k, v) in lines}

# === BLOCK 4 (label=human, source_idx=line1998_human, name=set_local_interface) ===
def set_local_interface(self, value=None, default=False, disable=False):
        """Configures the mlag local-interface value

        Args:
            value (str): The value to configure the local-interface
            default (bool): Configures the local-interface using the
                default keyword
            disable (bool): Negates the local-interface using the no keyword

        Returns:
            bool: Returns True if the commands complete successfully
        """
        return self._configure_mlag('local-interface', value, default, disable)

# === BLOCK 5 (label=lm, source_idx=line2155_lm, name=_handle_chat_name) ===
def _handle_chat_name(self, data):
        """Handle user name changes"""
        user_id = data["user_id"]
        new_name = data["new_name"]
        self.users[user_id]["name"] = new_name

# === BLOCK 6 (label=human, source_idx=line590_human, name=and_next) ===
def and_next(e):
    """
    Create a PEG function for positive lookahead.
    """
    def match_and_next(s, grm=None, pos=0):
        try:
            e(s, grm, pos)
        except PegreError as ex:
            raise PegreError('Positive lookahead failed', pos)
        else:
            return PegreResult(s, Ignore, (pos, pos))
    return match_and_next
