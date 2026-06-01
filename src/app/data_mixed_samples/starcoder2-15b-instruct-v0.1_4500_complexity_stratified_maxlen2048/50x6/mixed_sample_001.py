# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2436_human, name=load) ===
def load(self, response):
        """Load the response and increment the counter.

        Args:
            response (:class:`.http.request.Response`): The response from
                a previous request.
        """
        self._response = response

        if self.next_location(raw=True):
            self._num_redirects += 1

# === BLOCK 2 (label=human, source_idx=line4891_human, name=shutdown_kernel) ===
def shutdown_kernel(self):
        """Shutdown the kernel of the client."""
        kernel_id = self.get_kernel_id()

        if kernel_id:
            delete_url = self.add_token(url_path_join(self.server_url,
                                                      'api/kernels/',
                                                      kernel_id))
            delete_req = requests.delete(delete_url)
            if delete_req.status_code != 204:
                QMessageBox.warning(
                    self,
                    _("Server error"),
                    _("The Jupyter Notebook server "
                      "failed to shutdown the kernel "
                      "associated with this notebook. "
                      "If you want to shut it down, "
                      "you'll have to close Spyder."))

# === BLOCK 3 (label=human, source_idx=line1169_human, name=update_configs) ===
def update_configs(self, release):
        """ Update the fedora-atomic.git repositories for a given release """
        git_repo = release['git_repo']
        git_cache = release['git_cache']
        if not os.path.isdir(git_cache):
            self.call(['git', 'clone', '--mirror', git_repo, git_cache])
        else:
            self.call(['git', 'fetch', '--all', '--prune'], cwd=git_cache)
        git_dir = release['git_dir'] = os.path.join(release['tmp_dir'],
                                                    os.path.basename(git_repo))
        self.call(['git', 'clone', '-b', release['git_branch'],
                   git_cache, git_dir])

        if release['delete_repo_files']:
            for repo_file in glob.glob(os.path.join(git_dir, '*.repo')):
                self.log.info('Deleting %s' % repo_file)
                os.unlink(repo_file)

# === BLOCK 4 (label=human, source_idx=line4349_human, name=_extract_proxies) ===
def _extract_proxies(self, ajax_endpoint):

        """ request the xml object """
        proxy_xml = requests.get(ajax_endpoint)
        print(proxy_xml.content)
        root = etree.XML(proxy_xml.content)
        quote = root.xpath('quote')[0]

# === BLOCK 5 (label=human, source_idx=line2279_human, name=no_positional) ===
def no_positional(allow_self=False):
    """A decorator that doesn't allow for positional arguments.

    :param bool allow_self:
        Whether to allow ``self`` as a positional argument.
    """
    def reject_positional_args(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            allowed_positional_args = 0
            if allow_self:
                allowed_positional_args = 1
            received_positional_args = len(args)
            if received_positional_args > allowed_positional_args:
                function_name = function.__name__
                verb = 'were' if received_positional_args > 1 else 'was'
                raise TypeError(('{}() takes {} positional arguments but {} '
                                 '{} given').format(
                                     function_name,
                                     allowed_positional_args,
                                     received_positional_args,
                                     verb,
                                ))
            return function(*args, **kwargs)
        return wrapper
    return reject_positional_args

# === BLOCK 6 (label=human, source_idx=line1678_human, name=rasterize) ===
def rasterize(self,
                  pitch,
                  origin,
                  resolution=None,
                  fill=True,
                  width=None,
                  **kwargs):
        """
        Rasterize a Path2D object into a boolean image ("mode 1").

        Parameters
        ------------
        pitch:      float, length in model space of a pixel edge
        origin:     (2,) float, origin position in model space
        resolution: (2,) int, resolution in pixel space
        fill:       bool, if True will return closed regions as filled
        width:      int, if not None will draw outline this wide (pixels)

        Returns
        ------------
        raster: PIL.Image object, mode 1
        """
        image = raster.rasterize(self,
                                 pitch=pitch,
                                 origin=origin,
                                 resolution=resolution,
                                 fill=fill,
                                 width=width)
        return image
