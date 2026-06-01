# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line317_lm, name=SerializeFaultDetail) ===
def SerializeFaultDetail(self, val, info):
      """ Serialize an object """
      return self.Serialize(val, info)

# === BLOCK 2 (label=lm, source_idx=line6358_lm, name=valueAt) ===
def valueAt(self, percent):
        """
        Returns the value at the inputed percent.

        :param     percent | <float>

        :return     <variant>
        """
        return self.valueAt(percent)

# === BLOCK 3 (label=human, source_idx=line6044_human, name=_tscube_app) ===
def _tscube_app(self, xmlfile):
        """Run gttscube as an application."""

        xmlfile = self.get_model_path(xmlfile)

        outfile = os.path.join(self.config['fileio']['workdir'],
                               'tscube%s.fits' % (self.config['file_suffix']))

        kw = dict(cmap=self.files['ccube'],
                  expcube=self.files['ltcube'],
                  bexpmap=self.files['bexpmap'],
                  irfs=self.config['gtlike']['irfs'],
                  evtype=self.config['selection']['evtype'],
                  srcmdl=xmlfile,
                  nxpix=self.npix, nypix=self.npix,
                  binsz=self.config['binning']['binsz'],
                  xref=float(self.roi.skydir.ra.deg),
                  yref=float(self.roi.skydir.dec.deg),
                  proj=self.config['binning']['proj'],
                  stlevel=0,
                  coordsys=self.config['binning']['coordsys'],
                  outfile=outfile)

        run_gtapp('gttscube', self.logger, kw)

# === BLOCK 4 (label=human, source_idx=line2648_human, name=create_date) ===
def create_date(past=False, max_years_future=10, max_years_past=10):
    """
    Create a random valid date
    If past, then dates can be in the past
    If into the future, then no more than max_years into the future
    If it's not, then it can't be any older than max_years_past
    """
    if past:
        start = datetime.datetime.today() - datetime.timedelta(days=max_years_past * 365)
        #Anywhere between 1980 and today plus max_ears
        num_days = (max_years_future * 365) + start.day
    else:
        start = datetime.datetime.today()
        num_days = max_years_future * 365

    random_days = random.randint(1, num_days)
    random_date = start + datetime.timedelta(days=random_days)
    return(random_date)

# === BLOCK 5 (label=human, source_idx=line3731_human, name=del_view_menu) ===
def del_view_menu(self, name):
        """
            Deletes a ViewMenu from the backend

            :param name:
                name of the ViewMenu
        """
        obj = self.find_view_menu(name)
        if obj:
            try:
                obj.delete()
            except Exception as e:
                log.error(c.LOGMSG_ERR_SEC_DEL_PERMISSION.format(str(e)))

# === BLOCK 6 (label=lm, source_idx=line6206_lm, name=to_utc_datetime) ===
def to_utc_datetime(self, value):
        """
        from value to datetime with tzinfo format (datetime.datetime instance)
        """
        return self.to_datetime(value).replace(tzinfo=pytz.utc)
