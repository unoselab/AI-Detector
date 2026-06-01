# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line675_lm, name=SerializeExclusiveData) ===
def SerializeExclusiveData(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        writer.WriteInt32(self._exclusive_data_length)
        writer.WriteBytes(self._exclusive_data)

# === BLOCK 2 (label=human, source_idx=line3313_human, name=export) ===
def export(self, location):
        """
        Export the Bazaar repository at the url to the destination location
        """
        # Remove the location to make sure Bazaar can export it correctly
        if os.path.exists(location):
            rmtree(location)

        with TempDirectory(kind="export") as temp_dir:
            self.unpack(temp_dir.path)

            self.run_command(
                ['export', location],
                cwd=temp_dir.path, show_stdout=False,
            )

# === BLOCK 3 (label=lm, source_idx=line4719_lm, name=delete_action) ===
def delete_action(self, action, player_idx=0):
        """
        Return a new `Player` instance with the action(s) specified by
        `action` deleted from the action set of the player specified by
        `player_idx`. Deletion is not performed in place.

        Parameters
        ----------
        action : scalar(int) or array_like(int)
            Integer or array like of integers representing the action(s)
            to be deleted.

        player_idx : scalar(int), optional(default=0)
            Index of the player to delete action(s) for.

        Returns
        -------
        Player
            Copy of `self` with the action(s) deleted as specified.

        Examples
        --------
        >>> player = Player([[3, 0], [0, 3], [1, 1]])
        >>> player
        Player([[3, 0],
                [0, 3],
                [1, 1]])
        >>> player.delete_action(2)
        Player([[3, 0],
                [0, 3]])
        >>> player.delete_action(0, player_idx=1)
        Player([[0],
                [3],
                [1]])

        """
        import numpy as np
        import copy

        new_player = copy.deepcopy(self)
        actions_to_delete = np.atleast_1d(action)

        current_actions = np.array(new_player.action_set[player_idx])
        mask = np.isin(current_actions, actions_to_delete, invert=True)
        new_player.action_set[player_idx] = current_actions[mask].tolist()

        return new_player

# === BLOCK 4 (label=human, source_idx=line8518_human, name=authenticate_redirect) ===
async def authenticate_redirect(self, callback_uri: str = None) -> None:
        """Just like `~OAuthMixin.authorize_redirect`, but
        auto-redirects if authorized.

        This is generally the right interface to use if you are using
        Twitter for single-sign on.

        .. versionchanged:: 3.1
           Now returns a `.Future` and takes an optional callback, for
           compatibility with `.gen.coroutine`.

        .. versionchanged:: 6.0

           The ``callback`` argument was removed. Use the returned
           awaitable object instead.
        """
        http = self.get_auth_http_client()
        response = await http.fetch(
            self._oauth_request_token_url(callback_uri=callback_uri)
        )
        self._on_request_token(self._OAUTH_AUTHENTICATE_URL, None, response)

# === BLOCK 5 (label=lm, source_idx=line163_lm, name=get_desktop_for_window) ===
def get_desktop_for_window(self, window):
        """
        Get the desktop a window is on.
        Uses _NET_WM_DESKTOP of the EWMH spec.

        If your desktop does not support ``_NET_WM_DESKTOP``, then '*desktop'
        remains unmodified.

        :param wid: the window to query
        """
        try:
            desktop = self.get_window_property(window, '_NET_WM_DESKTOP')
            if desktop is not None:
                return desktop[0]
        except Exception:
            pass
        return None

# === BLOCK 6 (label=human, source_idx=line5895_human, name=_get_dcd) ===
def _get_dcd(self, alias):
        """
        Get the Docker-Content-Digest header for an alias.

        :param alias: Alias name.
        :type alias: str

        :rtype: str
        :returns: DCD header for the alias.
        """
        # https://docs.docker.com/registry/spec/api/#deleting-an-image
        # Note When deleting a manifest from a registry version 2.3 or later,
        # the following header must be used when HEAD or GET-ing the manifest
        # to obtain the correct digest to delete:
        # Accept: application/vnd.docker.distribution.manifest.v2+json
        return self._request(
            'head',
            'manifests/{}'.format(alias),
            headers={'Accept': _schema2_mimetype},
        ).headers.get('Docker-Content-Digest')
