# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line871_lm, name=transform_audio) ===
def transform_audio(self, y):
        """Compute the STFT

        Parameters
        ----------
        y : np.ndarray
            The audio buffer

        Returns
        -------
        data : dict
            data['mag'] : np.ndarray, shape=(n_frames, 1 + n_fft//2)
                The STFT magnitude
        """
        def transform_audio(self, y):
            D = np.abs(self.stft(y))
            return {'mag': D}

# === BLOCK 2 (label=lm, source_idx=line1222_lm, name=start_runtime) ===
def start_runtime(self):
        """
        Start the system!
        """
        self.initialize_system()
        self.load_configuration()
        self.start_services()
        self.start_monitoring()

# === BLOCK 3 (label=lm, source_idx=line1150_lm, name=run) ===
def run(self):
        """
        This is the general passive maintenance process controller for the Salt
        master.

        This is where any data that needs to be cleanly maintained from the
        master is maintained.
        """

# === BLOCK 4 (label=lm, source_idx=line1371_lm, name=startAlertListener) ===
def startAlertListener(self, callback=None):
        """ Creates a websocket connection to the Plex Server to optionally recieve
            notifications. These often include messages from Plex about media scans
            as well as updates to currently running Transcode Sessions.

            NOTE: You need websocket-client installed in order to use this feature.
            >> pip install websocket-client

            Parameters:
                callback (func): Callback function to call on recieved messages.

            raises:
                :class:`plexapi.exception.Unsupported`: Websocket-client not installed.
        """
        try:
            import websocket
        except ImportError:
            raise Unsupported('Websocket-client not installed. Run "pip install websocket-client" to install.')

        if not self.websocketUrl:
            raise Unsupported('The Plex Server does not support the alert/notify feature.')

        def on_message(ws, message):
            if callback:
                callback(message)

        def on_error(ws, error):
            print(error)

        def on_close(ws):
            print("Websocket closed")

        def on_open(ws):
            print("Websocket opened")

        ws = websocket.WebSocketApp(self.websocketUrl,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        ws.on_open = on_open
        ws.run_forever()

# === BLOCK 5 (label=lm, source_idx=line400_lm, name=get_rmetric) ===
def get_rmetric( self, mode_inv = 'svd', return_svd = False ):
        """
        Compute the Reimannian Metric
        """
        if mode_inv =='svd':
            U, S, V = np.linalg.svd(self.R)
            S_inv = np.diag(1. / S)
            R_inv = V.dot(S_inv).dot(U.T)
        elif mode_inv == 'pinv':
            R_inv = np.linalg.pinv(self.R)
        else:
            raise ValueError("Invalid mode_inv: must be'svd' or 'pinv'")

        if return_svd:
            return R_inv, U, S, V
        else:
            return R_inv

# === BLOCK 6 (label=lm, source_idx=line2241_lm, name=dict_chunks) ===
def dict_chunks(dictionary, chunk):
    """Return a list of dictionary with n-keys (chunk) per list."""
    result = []
    for key in dictionary:
        if not result or len(result[-1]) == chunk:
            result.append({})
        result[-1][key] = dictionary[key]
    return result
