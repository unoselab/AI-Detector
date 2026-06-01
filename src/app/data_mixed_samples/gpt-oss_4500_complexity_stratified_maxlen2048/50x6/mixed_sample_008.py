# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3128_lm, name=fetch_room_ids) ===
def fetch_room_ids(self, names):
        """ Fetches the ids of the rooms with the given names """
        # Cache room name-to-id mapping to avoid repeated API calls
        if not hasattr(self, "_room_name_to_id"):
            try:
                rooms = self.client.rooms.list()
            except Exception:
                rooms = []
            self._room_name_to_id = {room.get("title"): room.get("id") for room in rooms if "title" in room and "id" in room}
        name_to_id = self._room_name_to_id

        # Preserve the order of the input names; return None for missing rooms
        return [name_to_id.get(name) for name in names]

# === BLOCK 2 (label=lm, source_idx=line6202_lm, name=phi) ===
def phi(self):
        """get the weighted total objective function

        Returns
        -------
        phi : float
            sum of squared residuals

        """
        import numpy as np
        r = np.asarray(self.residuals)
        # Prefer explicit weight attribute if present
        if hasattr(self, "weights"):
            w = np.asarray(self.weights)
            if w.ndim == 1:
                return float(np.dot(w, r ** 2))
            else:
                return float(r @ w @ r)
        if hasattr(self, "W"):
            W = np.asarray(self.W)
            return float(r @ W @ r)
        # Unweighted sum of squares
        return float(np.dot(r, r))

# === BLOCK 3 (label=human, source_idx=line5884_human, name=AvgPooling) ===
def AvgPooling(
        inputs,
        pool_size,
        strides=None,
        padding='valid',
        data_format='channels_last'):
    """
    Same as `tf.layers.AveragePooling2D`. Default strides is equal to pool_size.
    """
    if strides is None:
        strides = pool_size
    layer = tf.layers.AveragePooling2D(pool_size, strides, padding=padding, data_format=data_format)
    ret = layer.apply(inputs, scope=tf.get_variable_scope())
    return tf.identity(ret, name='output')

# === BLOCK 4 (label=human, source_idx=line2618_human, name=render) ===
def render(data, saltenv='base', sls='', argline='', **kwargs):  # pylint: disable=unused-argument
    """
    Decrypt the data to be rendered that was encrypted using AWS KMS envelope encryption.
    """
    translate_newlines = kwargs.get('translate_newlines', False)
    return _decrypt_object(data, translate_newlines=translate_newlines)

# === BLOCK 5 (label=human, source_idx=line3821_human, name=upload_output_to_s3) ===
def upload_output_to_s3(job, job_vars):
    """
    If s3_dir is specified in arguments, file will be uploaded to S3 using boto.
    WARNING: ~/.boto credentials are necessary for this to succeed!

    job_vars: tuple     Tuple of dictionaries: input_args and ids
    """
    import boto
    from boto.s3.key import Key

    input_args, ids = job_vars
    work_dir = job.fileStore.getLocalTempDir()
    uuid = input_args['uuid']
    # Parse s3_dir
    s3_dir = input_args['s3_dir']
    bucket_name = s3_dir.split('/')[0]
    bucket_dir = '/'.join(s3_dir.split('/')[1:])
    # I/O
    uuid_tar = return_input_paths(job, work_dir, ids, 'uuid.tar.gz')
    # Upload to S3 via boto
    conn = boto.connect_s3()
    bucket = conn.get_bucket(bucket_name)
    k = Key(bucket)
    k.key = os.path.join(bucket_dir, uuid + '.tar.gz')
    k.set_contents_from_filename(uuid_tar)

# === BLOCK 6 (label=lm, source_idx=line6093_lm, name=interpolate_xml_array) ===
def interpolate_xml_array(data, low_res_coords, shape, chunks):
        """Interpolate arbitrary size dataset to a full sized grid."""
        import numpy as np
        from scipy.interpolate import griddata

        try:
            import dask.array as da
        except Exception:  # pragma: no cover
            da = None

        # Ensure inputs are numpy arrays
        data = np.asarray
