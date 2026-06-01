# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line5165_lm, name=register_models) ===
def register_models(self, *models, **kwargs):
        """
        Register multiple models with the same
        arguments.

        Calls register for each argument passed along with
        all keyword arguments.
        """
        for model in models:
            self.register(model, **kwargs)

# === BLOCK 2 (label=human, source_idx=line6017_human, name=orthogonal_initialization) ===
def orthogonal_initialization(X,K):
    """
    Initialize the centrodis by orthogonal_initialization.
    Parameters    
    --------------------
    X(data): array-like, shape= (m_samples,n_samples)
    K: integer
        number of K clusters   
    Returns
    -------
    centroids: array-like, shape (K,n_samples)  
    data_norms: array-like, shape=(1,n_samples)     
    """
    N,M = X.shape
    centroids= X[np.random.randint(0, N-1,1),:] 
    data_norms = np.linalg.norm(X, axis = 1)# contains the norm of each data point, only do this once

    center_norms = np.linalg.norm(centroids, axis=1) # contains the norms of the centers, will need to be updated when new center added

    for k in range(1,K):    
        ## Here's where we compute the cosine of the angle between them:
        # Compute the dot (inner) product between each data point and each center
        new_center_index,new_center = new_orthogonal_center(X,data_norms,centroids,center_norms =center_norms)
        centroids = np.vstack((centroids,new_center))          
        center_norms = np.hstack((center_norms,data_norms[new_center_index]))   
    return centroids,data_norms

# === BLOCK 3 (label=lm, source_idx=line5981_lm, name=draw_on) ===
def draw_on(self, canvas, stem_color, leaf_color, thickness, ages=None):
        """Draw the tree on a canvas.

        Args:
            canvas (object): The canvas, you want to draw the tree on. Supported canvases: svgwrite.Drawing and PIL.Image (You can also add your custom libraries.)
            stem_color (tupel): Color or gradient for the stem of the tree.
            leaf_color (tupel): Color for the leaf (= the color for last iteration).
            thickness (int): The start thickness of the tree.
        """
        if isinstance(canvas, svgwrite.Drawing):
            self.draw_on_svg(canvas, stem_color, leaf_color, thickness, ages)
        elif isinstance(canvas, PIL.Image):
            self.draw_on_pil(canvas, stem_color, leaf_color, thickness, ages)
        else:
            raise TypeError("The canvas must be an instance of svgwrite.Drawing or PIL.Image.")

# === BLOCK 4 (label=lm, source_idx=line2706_lm, name=namespace_uri) ===
def namespace_uri(self):
        """
        Finds and returns first applied URI of this node that has a namespace.

        :return str: uri
        """
        return self.find_first_applied_uri(self.namespace_uri)

# === BLOCK 5 (label=human, source_idx=line6107_human, name=_replace_pg_hba) ===
def _replace_pg_hba(self):
        """
        Replace pg_hba.conf content in the PGDATA if hba_file is not defined in the
        `postgresql.parameters` and pg_hba is defined in `postgresql` configuration section.

        :returns: True if pg_hba.conf was rewritten.
        """

        # when we are doing custom bootstrap we assume that we don't know superuser password
        # and in order to be able to change it, we are opening trust access from a certain address
        if self._running_custom_bootstrap:
            addresses = {'': 'local'}
            if 'host' in self._local_address and not self._local_address['host'].startswith('/'):
                for _, _, _, _, sa in socket.getaddrinfo(self._local_address['host'], self._local_address['port'],
                                                         0, socket.SOCK_STREAM, socket.IPPROTO_TCP):
                    addresses[sa[0] + '/32'] = 'host'

            with open(self._pg_hba_conf, 'w') as f:
                f.write(self._CONFIG_WARNING_HEADER)
                for address, t in addresses.items():
                    f.write((
                        '{0}\treplication\t{1}\t{3}\ttrust\n'
                        '{0}\tall\t{2}\t{3}\ttrust\n'
                    ).format(t, self._replication['username'], self._superuser.get('username') or 'all', address))
        elif not self._server_parameters.get('hba_file') and self.config.get('pg_hba'):
            with open(self._pg_hba_conf, 'w') as f:
                f.write(self._CONFIG_WARNING_HEADER)
                for line in self.config['pg_hba']:
                    f.write('{0}\n'.format(line))
            return True

# === BLOCK 6 (label=human, source_idx=line3440_human, name=restore) ===
def restore(self, fade=False):
        """Restore the state of a device to that which was previously saved.

        For coordinator devices restore everything. For slave devices
        only restore volume etc., not transport info (transport info
        comes from the slave's coordinator).

        Args:
            fade (bool): Whether volume should be faded up on restore.
        """

        try:
            if self.is_coordinator:
                self._restore_coordinator()
        finally:
            self._restore_volume(fade)

        # Now everything is set, see if we need to be playing, stopped
        # or paused ( only for coordinators)
        if self.is_coordinator:
            if self.transport_state == 'PLAYING':
                self.device.play()
            elif self.transport_state == 'STOPPED':
                self.device.stop()
