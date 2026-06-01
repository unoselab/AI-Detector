# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line5077_human, name=route_not_found) ===
def route_not_found(*args):
        """
        Constructs a Flask Response for when a API Route (path+method) is not found. This is usually
        HTTP 404 but with API Gateway this is a HTTP 403 (https://forums.aws.amazon.com/thread.jspa?threadID=2166840)

        :return: a Flask Response
        """
        response_data = jsonify(ServiceErrorResponses._MISSING_AUTHENTICATION)
        return make_response(response_data, ServiceErrorResponses.HTTP_STATUS_CODE_403)

# === BLOCK 2 (label=human, source_idx=line3508_human, name=save_configs) ===
def save_configs(self):
        """
        Saves the startup-config and private-config to files.
        """

        try:
            config_path = os.path.join(self._working_directory, "configs")
            os.makedirs(config_path, exist_ok=True)
        except OSError as e:
            raise DynamipsError("Could could not create configuration directory {}: {}".format(config_path, e))

        startup_config_base64, private_config_base64 = yield from self.extract_config()
        if startup_config_base64:
            startup_config = self.startup_config_path
            try:
                config = base64.b64decode(startup_config_base64).decode("utf-8", errors="replace")
                config = "!\n" + config.replace("\r", "")
                config_path = os.path.join(self._working_directory, startup_config)
                with open(config_path, "wb") as f:
                    log.info("saving startup-config to {}".format(startup_config))
                    f.write(config.encode("utf-8"))
            except (binascii.Error, OSError) as e:
                raise DynamipsError("Could not save the startup configuration {}: {}".format(config_path, e))

        if private_config_base64 and base64.b64decode(private_config_base64) != b'\nkerberos password \nend\n':
            private_config = self.private_config_path
            try:
                config = base64.b64decode(private_config_base64).decode("utf-8", errors="replace")
                config_path = os.path.join(self._working_directory, private_config)
                with open(config_path, "wb") as f:
                    log.info("saving private-config to {}".format(private_config))
                    f.write(config.encode("utf-8"))
            except (binascii.Error, OSError) as e:
                raise DynamipsError("Could not save the private configuration {}: {}".format(config_path, e))

# === BLOCK 3 (label=lm, source_idx=line2868_lm, name=make_folder_for_today) ===
def make_folder_for_today(log_dir):
    """Creates the folder log_dir/yyyy/mm/dd in log_dir if it doesn't exist
    and returns the full path of the folder."""
    today = datetime.datetime.today()
    today_folder = os.path.join(log_dir, str(today.year), str(today.month), str(today.day))
    if not os.path.exists(today_folder):
        os.makedirs(today_folder)
    return today_folder

# === BLOCK 4 (label=lm, source_idx=line2419_lm, name=write_pid_file) ===
def write_pid_file():
    """Write a file with the PID of this server instance.

    Call when setting up a command line testserver.
    """
    pid = os.getpid()
    with open(PID_FILE, 'w') as f:
        f.write(str(pid))

# === BLOCK 5 (label=human, source_idx=line4248_human, name=compose) ===
def compose(self, bbox=None, **kwargs):
        """
        Compose the artboard.

        See :py:func:`~psd_tools.compose` for available extra arguments.

        :param bbox: Viewport tuple (left, top, right, bottom).
        :return: :py:class:`PIL.Image`, or `None` if there is no pixel.
        """
        from psd_tools.api.composer import compose
        return compose(self, bbox=bbox or self.bbox, **kwargs)

# === BLOCK 6 (label=lm, source_idx=line3848_lm, name=df_to_dat) ===
def df_to_dat(net, df, define_cat_colors=False):
  """
  This is always run when data is loaded.
  """
  # This is the data that will be used to define the network.
  # It is a list of dictionaries, each dictionary is a node.
  # Each node has a 'name' key, and a 'color' key.
  # The 'color' key is a list of colors, one for each category.
  # If a node has a'size' key, it will be used to scale the node size.
  # If a node has a'shape' key, it will be used to set the node shape.
  # If a node has a 'label' key, it will be used to set the node label.
  # If a node has a 'label_size' key, it will be used to set the node label size.
  # If a node has a 'label_color' key, it will be used to set the node label color.
  # If a node has a 'label_background_color' key, it will be used to set the node label background color.
  # If a node has a 'label_background_opacity' key, it will be used to set the node label background opacity.
  # If a node has a 'label_font_weight' key, it will be used to set the node label font weight.
  # If a node has a 'label_font_style' key, it will be used to set the node label font style.
  # If a node has a 'label_font_family' key, it will be used to set the node label font family.
  # If a node has a 'label_font_size' key, it will be used to set the node label font size.
  # If a node has a 'label_font_color' key, it will be used to set the node label font color.
  # If a node has a 'label_font_background_color' key, it will be used to set the node label font background color.
  # If a node has a 'label_font_background_opacity' key, it will be used to set the node label font background opacity.
  # If a node has a 'label_font_weight' key, it will be used to set the node label font weight.
  # If a node has a 'label_font_style' key, it will be used to set the node label font style.
  # If a node has a 'label_font_family' key,
