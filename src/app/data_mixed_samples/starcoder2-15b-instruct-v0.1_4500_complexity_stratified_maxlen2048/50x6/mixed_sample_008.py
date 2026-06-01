# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line250_lm, name=find_child_element) ===
def find_child_element(elm, child_local_name):
    """
    Find an XML child element by local tag name.
    """
    for child in elm:
        if child.tag.split('}')[-1] == child_local_name:
            return child
    return None

# === BLOCK 2 (label=lm, source_idx=line4891_lm, name=shutdown_kernel) ===
def shutdown_kernel(self):
        """Shutdown the kernel of the client."""
        self.kernel_client.shutdown_kernel()

# === BLOCK 3 (label=human, source_idx=line4663_human, name=layer_norm_compute) ===
def layer_norm_compute(x, epsilon, scale, bias, layer_collection=None):
  """Layer norm raw computation."""

  # Save these before they get converted to tensors by the casting below
  params = (scale, bias)

  epsilon, scale, bias = [cast_like(t, x) for t in [epsilon, scale, bias]]
  mean = tf.reduce_mean(x, axis=[-1], keepdims=True)
  variance = tf.reduce_mean(
      tf.squared_difference(x, mean), axis=[-1], keepdims=True)
  norm_x = (x - mean) * tf.rsqrt(variance + epsilon)

  output = norm_x * scale + bias


  return output

# === BLOCK 4 (label=human, source_idx=line2129_human, name=get_queryset) ===
def get_queryset(self, **kwargs):
        """
        Gets our queryset.  This takes care of filtering if there are any
        fields to filter by.
        """
        queryset = self.derive_queryset(**kwargs)

        return self.order_queryset(queryset)

# === BLOCK 5 (label=human, source_idx=line3018_human, name=creation_time) ===
def creation_time(self, timeformat='unix'):
        """Returns the UTC time of creation of this aggregated measurement

        :param timeformat: the format for the time value. May be:
            '*unix*' (default) for UNIX time, '*iso*' for ISO8601-formatted
            string in the format ``YYYY-MM-DD HH:MM:SS+00`` or `date` for
            a ``datetime.datetime`` object
        :type timeformat: str
        :returns: an int or a str or a ``datetime.datetime`` object or None
        :raises: ValueError

        """
        if self.timestamp is None:
            return None
        return timeformatutils.timeformat(self.timestamp, timeformat)

# === BLOCK 6 (label=lm, source_idx=line4809_lm, name=find_base_images) ===
def find_base_images(self):
        """Finds all mountpoints that are mounted to a directory matching :attr:`orig_re_pattern`."""
        base_images = []
        for mountpoint in self.mountpoints:
            if re.match(self.orig_re_pattern, mountpoint.mount_path):
                base_images.append(mountpoint)
        return base_images
