# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1536_human, name=getnames) ===
def getnames():
    """
    get mail names
    """
    namestring = ""
    addmore = 1
    while addmore:
        scientist = input("Enter  name  - <Return> when done ")
        if scientist != "":
            namestring = namestring + ":" + scientist
        else:
            namestring = namestring[1:]
            addmore = 0
    return namestring

# === BLOCK 2 (label=lm, source_idx=line3529_lm, name=schemes) ===
def schemes(self):
        """Return supported schemes."""
        return self.schemes

# === BLOCK 3 (label=human, source_idx=line3013_human, name=partition_metadata) ===
def partition_metadata(self, partition_key):
        """
        Retrieves the metadata dictionary for the remote database partition.

        :param str partition_key: Partition key.
        :returns: Metadata dictionary for the database partition.
        :rtype: dict
        """
        resp = self.r_session.get(self.database_partition_url(partition_key))
        resp.raise_for_status()
        return response_to_json_dict(resp)

# === BLOCK 4 (label=lm, source_idx=line5179_lm, name=push) ===
def push(self, my_dict, key, element):
        """ Push an element onto an array that may not have been defined in
        the dict """
        if key in my_dict:
            my_dict[key].append(element)
        else:
            my_dict[key] = [element]

# === BLOCK 5 (label=lm, source_idx=line6756_lm, name=list_tags) ===
def list_tags(self, image_name):
        # type: (str) -> Iterator[str]
        """ List all tags for the given image stored in the registry.

        Args:
            image_name (str):
                The name of the image to query. The image must be present on the
                registry for this call to return any values.
        Returns:
            list[str]: List of tags for that image.
        """
        return self._list_tags(image_name)

# === BLOCK 6 (label=human, source_idx=line529_human, name=profile_tilt) ===
def profile_tilt(data, mask):
    """Fit a 2D tilt to `data[mask]`"""
    params = lmfit.Parameters()
    params.add(name="mx", value=0)
    params.add(name="my", value=0)
    params.add(name="off", value=np.average(data[mask]))
    fr = lmfit.minimize(tilt_residual, params, args=(data, mask))
    bg = tilt_model(fr.params, data.shape)
    return bg
