# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4145_human, name=from_shapefile) ===
def from_shapefile(output, input_shp_files, validate):
    """
    Convert multiple ESRI Shapefile(s) into a single NRML source model file.
    """
    input_parser = shapefileparser.ShapefileParser()
    source_model = input_parser.read(input_shp_files[0], validate)
    for f in input_shp_files[1:]:
        source_model.sources.extend(input_parser.read(f, validate).sources)
    if not output:
        output = os.path.splitext(input_shp_files[0])[0]
    shapefileparser.SourceModelParser().write(output + '.xml', source_model)

# === BLOCK 2 (label=lm, source_idx=line8901_lm, name=accounts) ===
def accounts(dbpath, output, format, account,
             config=None, tag=None, tagprefix=None, region=(),
             not_region=(), not_bucket=None):
    """Report on stats by account"""
    db = get_db(dbpath)
    if not db:
        return
    if not account:
        print("Error: must specify --account")
        return
    if not format:
        print("Error: must specify --format")
        return
    if not output:
        print("Error: must specify --output")
        return
    if config:
        config = get_config(config)
    else:
        config = {}
    if tag:
        if not tagprefix:
            print("Error: must specify --tagprefix")
            return
        tag = tagprefix + tag
    if not region:
        region = get_region(config)
    if not not_region:
        not_region = get_not_region(config)
    if not_bucket:
        not_bucket = get_not_bucket(config)
    if not config:
        config = {}
    if not config.get('accounts'):
        print("Error: must specify --accounts in config")
        return
    if not config.get('buckets'):
        print("Error: must specify --buckets in config")
        return
    if not config.get('regions'):
        print("Error: must specify --regions in config")
        return
    if not config.get('not_regions'):
        print("Error: must specify --not_regions in config")
        return
    if not config.get('not_buckets'):
        print("Error: must specify --not_buckets in config")
        return
    if not config.get('account_tag'):
        print("Error: must specify --account_tag in config")
        return
    if not config.get('bucket_tag'):
        print("Error: must specify --bucket_tag in config")
        return
    if not config.get('region_tag'):
        print("Error: must specify --region_tag in config")
        return
    if not config.get('not_region_tag'):
        print("Error: must specify --not_region_tag in config")
        return
    if not config.get('not_bucket_tag'):
        print("Error: must specify --not_bucket_tag in config")

# === BLOCK 3 (label=human, source_idx=line3961_human, name=newCharRef) ===
def newCharRef(self, name):
        """Creation of a new character reference node. """
        ret = libxml2mod.xmlNewCharRef(self._o, name)
        if ret is None:raise treeError('xmlNewCharRef() failed')
        __tmp = xmlNode(_obj=ret)
        return __tmp

# === BLOCK 4 (label=human, source_idx=line6096_human, name=_resize_blob) ===
def _resize_blob(self, ud, size):
        # type: (Uploader, blobxfer.models.upload.Descriptor, int) -> None
        """Resize page blob
        :param Uploader self: this
        :param blobxfer.models.upload.Descriptor ud: upload descriptor
        :param int size: content length
        """
        blobxfer.operations.azure.blob.page.resize_blob(ud.entity, size)
        if blobxfer.util.is_not_empty(ud.entity.replica_targets):
            for ase in ud.entity.replica_targets:
                blobxfer.operations.azure.blob.page.resize_blob(ase, size)

# === BLOCK 5 (label=lm, source_idx=line584_lm, name=set_custom_value) ===
def set_custom_value(custom_name, custom_val):
    """
    Set a custom value to be given back in the feedback
    :param custom_name: name/key of the entry to be placed in the custom dict
    :param custom_val: content of the entry to be placed in the custom dict
    """
    custom_dict = get_custom_dict()
    custom_dict[custom_name] = custom_val

# === BLOCK 6 (label=lm, source_idx=line7301_lm, name=predict_y) ===
def predict_y(self, xq, sigma=None, k=None, **kwargs):
        """Provide an prediction of xq in the output space

        @param xq  an array of float of length dim_x
        """
        if sigma is None:
            sigma = self.sigma
        if k is None:
            k = self.k
        if self.sigma_f is None:
            raise ValueError("No sigma_f defined")
        if self.sigma_n is None:
            raise ValueError("No sigma_n defined")
        if self.sigma_d is None:
            raise ValueError("No sigma_d defined")
        if self.sigma_m is None:
            raise ValueError("No sigma_m defined")
        if self.sigma_f is None:
            raise ValueError("No sigma_f defined")
        if self.sigma_n is None:
            raise ValueError("No sigma_n defined")
        if self.sigma_d is None:
            raise ValueError("No sigma_d defined")
        if self.sigma_m is None:
            raise ValueError("No sigma_m defined")
        if self.sigma_f is None:
            raise ValueError("No sigma_f defined")
        if self.sigma_n is None:
            raise ValueError("No sigma_n defined")
        if self.sigma_d is None:
            raise ValueError("No sigma_d defined")
        if self.sigma_m is None:
            raise ValueError("No sigma_m defined")
        if self.sigma_f is None:
            raise ValueError("No sigma_f defined")
        if self.sigma_n is None:
            raise ValueError("No sigma_n defined")
        if self.sigma_d is None:
            raise ValueError("No sigma_d defined")
        if self.sigma_m is None:
            raise ValueError("No sigma_m defined")
        if self.sigma_f is None:
            raise ValueError("No sigma_f defined")
        if self.sigma_n is None:
            raise ValueError("No sigma_n defined")
        if self.sigma_d is None:
            raise ValueError("No sigma_d defined")
        if self.sigma_m is None:
            raise ValueError("No sigma_m defined")
