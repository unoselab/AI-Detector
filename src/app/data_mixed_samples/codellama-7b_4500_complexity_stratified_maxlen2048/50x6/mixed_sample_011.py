# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line484_human, name=get_start_and_end_time) ===
def get_start_and_end_time(self, ref=None):
        """Specific function to get start time and end time for StandardDaterange

        :param ref: time in seconds
        :type ref: int
        :return: tuple with start and end time
        :rtype: tuple (int, int)
        """
        now = time.localtime(ref)
        self.syear = now.tm_year
        self.month = now.tm_mon
        self.wday = now.tm_wday
        day_id = Daterange.get_weekday_id(self.day)
        today_morning = get_start_of_day(now.tm_year, now.tm_mon, now.tm_mday)
        tonight = get_end_of_day(now.tm_year, now.tm_mon, now.tm_mday)
        day_diff = (day_id - now.tm_wday) % 7
        morning = datetime.fromtimestamp(today_morning) + timedelta(days=day_diff)
        night = datetime.fromtimestamp(tonight) + timedelta(days=day_diff)
        return (int(morning.strftime("%s")), int(night.strftime("%s")))

# === BLOCK 2 (label=lm, source_idx=line2324_lm, name=get) ===
def get(self, uri):
        """
            Sends a GET request.

            @param uri: Uri of Service API.
            @param data: Requesting Data. Default: None

            @raise NetworkAPIClientError: Client failed to access the API.
        """
        return self._request(uri, 'GET')

# === BLOCK 3 (label=lm, source_idx=line2359_lm, name=refresh) ===
def refresh(self):
        """Refresh the server and it's child objects.

        This method removes all the cache information in the server
        and it's child objects, and fetches the information again from
        the server using hpssacli/ssacli command.

        :raises: HPSSAOperationError, if hpssacli/ssacli operation failed.
        """
        self.remove_all_properties()
        self.get_properties()

# === BLOCK 4 (label=human, source_idx=line5597_human, name=initialize) ===
async def initialize(self):
        """
         Initialize static data like images and flavores and set it as object property
        """
        flavors = await self._list_flavors()
        images = await self._list_images()

        self.flavors_map = bidict()
        self.images_map = bidict()
        self.images_details = {}

        for flavor in flavors:
            self.flavors_map.put(flavor['id'], flavor['name'], on_dup_key='OVERWRITE', on_dup_val='OVERWRITE')

        for image in images:
            # @TODO filetes :
            # @TODO filtering by owner
            # if hasattr(image, 'owner_id') and  image.owner_id in self.config['image_owner_ids']:
            #  @TODO enable filtering by tag
            # if 'lastest' in image.tags:
            self.images_details[image['id']] = {
                'name': image['name'],
                'created_at': image['created_at'],
                'latest': 'latest' in image['tags']
            }
            self.images_map.put(image['id'], image['name'], on_dup_key='OVERWRITE', on_dup_val='OVERWRITE')

# === BLOCK 5 (label=lm, source_idx=line3726_lm, name=tarfile_extract) ===
def tarfile_extract(fileobj, dest_path):
        """Extract a tarfile described by a file object to a specified path.

        Args:
            fileobj (file): File object wrapping the target tarfile.
            dest_path (str): Path to extract the contents of the tarfile to.
        """
        with tarfile.open(fileobj=fileobj, mode='r') as tar:
            tar.extractall(path=dest_path)

# === BLOCK 6 (label=human, source_idx=line7281_human, name=export) ===
def export(self, nidm_version, export_dir):
        """
        Create prov entities and activities.
        """

        # In FSL we have a single thresholding (extent, height) applied to all
        # contrasts
        # FIXME: Deal with two-tailed inference?
        atts = (
            (PROV['type'], self.type),
            (PROV['label'], self.label),
            (NIDM_HAS_ALTERNATIVE_HYPOTHESIS, self.tail))

        if self.partial_degree is not None:
            atts += (
                (SPM_PARTIAL_CONJUNCTION_DEGREE, self.partial_degree),)

        self.add_attributes(atts)
