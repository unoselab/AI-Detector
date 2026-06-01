# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line6390_human, name=get) ===
def get(self):
        """Return axes, graphics, and layout options."""
        options = {}
        for x in [self.axes, self.graphics, self.layout]:
            for k, v in list(x.get().items()):
                options[k] = v

        return options

# === BLOCK 2 (label=lm, source_idx=line3563_lm, name=pdf_mmd) ===
def pdf_mmd(self, lon, lat, mag_1, mag_2, distance_modulus, mask, delta_mag=0.03, steps=1000):
        """
        Ok, now here comes the beauty of having the signal MMD.
        """
        # First, we need to get the MMD for the signal.
        # We'll do this by getting the MMD for the signal at the same distance as the mask.
        # We'll then use the distance modulus to get the distance to the signal.
        # Then we'll get the MMD for the signal at that distance.
        # We'll then use the distance modulus to get the distance to the mask.
        # Then we'll get the MMD for the mask at that distance.
        # We'll then use the distance modulus to get the distance to the signal.
        # Then we'll get the MMD for the signal at that distance.
        # We'll then use the distance modulus to get the distance to the mask.
        # Then we'll get the MMD for the mask at that distance.
        # We'll then use the distance modulus to get the distance to the signal.
        # Then we'll get the MMD for the signal at that distance.
        # We'll then use the distance modulus to get the distance to the mask.
        # Then we'll get the MMD for the mask at that distance.
        # We'll then use the distance modulus to get the distance to the signal.
        # Then we'll get the MMD for the signal at that distance.
        # We'll then use the distance modulus to get the distance to the mask.
        # Then we'll get the MMD for the mask at that distance.
        # We'll then use the distance modulus to get the distance to the signal.
        # Then we'll get the MMD for the signal at that distance.
        # We'll then use the distance modulus to get the distance to the mask.
        # Then we'll get the MMD for the mask at that distance.
        # We'll then use the distance modulus to get the distance to the signal.
        # Then we'll get the MMD for the signal at that distance.
        # We'll then use the distance modulus to get the distance to the mask.
        # Then we'll get the MMD for the mask at that distance.
        # We'll then use the distance modulus to get the distance

# === BLOCK 3 (label=lm, source_idx=line5623_lm, name=line_width) ===
def line_width(default_width=DEFAULT_LINE_WIDTH, max_width=MAX_LINE_WIDTH):
    """
    Return the ideal column width for the output from :func:`see.see`, taking
    the terminal width into account to avoid wrapping.
    """
    width = default_width
    try:
        width = max(width, os.get_terminal_size().columns)
    except OSError:
        pass
    return min(width, max_width)

# === BLOCK 4 (label=lm, source_idx=line6384_lm, name=format_item) ===
def format_item(item, template, name='item'):
    """Render a template to a string with the provided item in context."""
    return template.render(**{name: item})

# === BLOCK 5 (label=human, source_idx=line5553_human, name=_update_dict) ===
def _update_dict(self, to_dict, from_dict):
        """ Recursively merges the fields for two dictionaries.

        Args:
            to_dict (dict): The dictionary onto which the merge is executed.
            from_dict (dict): The dictionary merged into to_dict
        """
        for key, value in from_dict.items():
            if key in to_dict and isinstance(to_dict[key], dict) and \
                    isinstance(from_dict[key], dict):
                self._update_dict(to_dict[key], from_dict[key])
            else:
                to_dict[key] = from_dict[key]

# === BLOCK 6 (label=human, source_idx=line280_human, name=parse_config_list) ===
def parse_config_list(config_list):
  """
  Parse a list of configuration properties separated by '='
  """
  if config_list is None:
    return {}
  else:
    mapping = {}
    for pair in config_list:
      if (constants.CONFIG_SEPARATOR not in pair) or (pair.count(constants.CONFIG_SEPARATOR) != 1):
        raise ValueError("configs must be passed as two strings separted by a %s", constants.CONFIG_SEPARATOR)
      (config, value) = pair.split(constants.CONFIG_SEPARATOR)
      mapping[config] = value
    return mapping
