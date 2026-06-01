# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4859_human, name=_process_get_status) ===
def _process_get_status(self, data):
        """ Processes a received STATUS message and notifies listeners. """
        status = self._parse_status(data, self.cast_type)
        is_new_app = self.app_id != status.app_id and self.app_to_launch
        self.status = status

        self.logger.debug("Received status: %s", self.status)
        self._report_status()

        if is_new_app and self.app_to_launch == self.app_id:
            self.app_to_launch = None
            self.app_launch_event.set()
            if self.app_launch_event_function:
                self.logger.debug("Start app_launch_event_function...")
                self.app_launch_event_function()
                self.app_launch_event_function = None

# === BLOCK 2 (label=human, source_idx=line4479_human, name=merge) ===
def merge(self, carts=None, new_cart_name=None):
        """
        `carts` - A list of cart names
        `new_cart_name` - Resultant cart name

        Merge the contents of N carts into a new cart

        TODO: Sanity check that each cart in `carts` exists. Try
        'juicer pull'ing carts that can't be located locally. Then cry
        like a baby and error out.
        """
        if new_cart_name is not None:
            cart_name = new_cart_name
        else:
            cart_name = carts[0]

        result_cart = juicer.common.Cart.Cart(cart_name)
        items_hash = {}
        for cart in carts:
            # 1. Grab items from each cart and shit them into result_cart
            tmpcart = juicer.common.Cart.Cart(cart, autoload=True)
            for repo, items in tmpcart.iterrepos():
                if str(repo) in [str(key) for key in items_hash.keys()]:
                    items_hash[str(repo)] += [str(item) for item in items]
                else:
                    items_hash[str(repo)] = [str(item) for item in items]
        # 2. Remove duplicates
        for key in items_hash.keys():
            items_hash[key] = list(set(items_hash[key]))
            # 3. Wrap it up
            result_cart[key] = items_hash[key]
        result_cart.save()
        # You can not fail at merging carts?
        return True

# === BLOCK 3 (label=lm, source_idx=line6096_lm, name=_resize_blob) ===
def _resize_blob(self, ud, size):
        # type: (Uploader, blobxfer.models.upload.Descriptor, int) -> None
        """Resize page blob
        :param Uploader self: this
        :param blobxfer.models.upload.Descriptor ud: upload descriptor
        :param int size: content length
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-branches
        # pylint: disable=to

# === BLOCK 4 (label=lm, source_idx=line2316_lm, name=_inherited_dashboard) ===
def _inherited_dashboard(dashboard, base_dashboards_from_pillar, ret):
    """Return a dashboard with properties from parents."""
    if dashboard in base_dashboards_from_pillar:
        ret.update(base_dashboards_from_pillar[dashboard])
    return ret

# === BLOCK 5 (label=human, source_idx=line6702_human, name=md5) ===
def md5(self):
        """
        MD5 of scene which will change when meshes or
        transforms are changed

        Returns
        --------
        hashed: str, MD5 hash of scene
        """
        # start with transforms hash
        hashes = [self.graph.md5()]
        for g in self.geometry.values():
            if hasattr(g, 'md5'):
                hashes.append(g.md5())
            elif hasattr(g, 'tostring'):
                hashes.append(str(hash(g.tostring())))
            else:
                # try to just straight up hash
                # this may raise errors
                hashes.append(str(hash(g)))

        md5 = util.md5_object(''.join(hashes))

        return md5

# === BLOCK 6 (label=lm, source_idx=line3304_lm, name=_lt_from_gt) ===
def _lt_from_gt(self, other):
    """Return a < b.  Computed by @total_ordering from (not a > b) and (a != b)."""
    assert not self.__eq__(other)
    return self.__lt__(other)
