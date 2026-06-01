# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line8201_lm, name=start) ===
def start(self, tcpport=102):
        """
        start the server.
        """
        import socket
        import threading

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', tcpport))
        self.server_socket.listen(5)

        def handle_client(conn, addr):
            try:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    conn.sendall(data)
            except Exception:
                pass
            finally:
                conn.close()

        def accept_loop():
            while True:
                try:
                    conn, addr = self.server_socket.accept()
                    thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                    thread.start()
                except Exception:
                    break

        self.server_thread = threading.Thread(target=accept_loop, daemon=True)
        self.server_thread.start()

# === BLOCK 2 (label=human, source_idx=line3493_human, name=wrap_get_user) ===
def wrap_get_user(cls, response):
        """Wrap the response from getting a user into an instance
        and return it

        :param response: The response from getting a user
        :type response: :class:`requests.Response`
        :returns: the new user instance
        :rtype: :class:`list` of :class:`User`
        :raises: None
        """
        json = response.json()
        u = cls.wrap_json(json)
        return u

# === BLOCK 3 (label=lm, source_idx=line1150_lm, name=scale_image) ===
def scale_image(image, new_width):
    """Resizes an image preserving the aspect ratio.
    """
    from PIL import Image
    width, height = image.size
    aspect_ratio = height / width
    new_height = int(new_width * aspect_ratio)
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

# === BLOCK 4 (label=human, source_idx=line6462_human, name=error) ===
def error(self, error):
        """
        set the error
        """
        # TODO: check length with value?
        # TODO: type checks (similar to value)
        if self.direction not in ['x', 'y', 'z'] and error is not None:
            raise ValueError("error only accepted for x, y, z dimensions")

        if isinstance(error, u.Quantity):
            error = error.to(self.unit).value

        self._error = error

# === BLOCK 5 (label=lm, source_idx=line7738_lm, name=enter_bootloader) ===
async def enter_bootloader(driver, model):
    """
    Using the driver method, enter bootloader mode of the atmega32u4.
    The bootloader mode opens a new port on the uC to upload the hex file.
    After receiving a 'dfu' command, the firmware provides a 3-second window to
    close the current port so as to do a clean switch to the bootloader port.
    The new port shows up as 'ttyn_bootloader' on the pi; upload fw through it.
    NOTE: Modules with old bootloader will have the bootloader port show up as
    a regular module port- 'ttyn_tempdeck'/ 'ttyn_magdeck' with the port number
    being either different or same as the one that the module was originally on
    So we check for changes in ports and use the appropriate one
    """
    import asyncio
    await asyncio.sleep(3)
    # The logic to detect the new port is handled by the driver's 
    # internal port management or the system's device discovery.
    # We return the driver instance or a status indicating the command was sent.
    return True

# === BLOCK 6 (label=human, source_idx=line6136_human, name=notice) ===
def notice(self, msg, *args, **kw):
        """Log a message with level :data:`NOTICE`. The arguments are interpreted as for :func:`logging.debug()`."""
        if self.isEnabledFor(NOTICE):
            self._log(NOTICE, msg, args, **kw)
