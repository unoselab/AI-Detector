# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line449_human, name=intersect) ===
def intersect(self, r):
        """Restrict self to common area with rectangle r."""
        if not len(r) == 4:
            raise ValueError("bad sequ. length")
        self.x0, self.y0, self.x1, self.y1 = TOOLS._intersect_rect(self, r)
        return self

# === BLOCK 2 (label=lm, source_idx=line2850_lm, name=get_list) ===
def get_list(medium, user, credentials):
    """Returns a MediumList (Anime or Manga depends on [medium]) of user.
    If user is not given, the username is taken from the initialized auth
    credentials.
    :param medium Anime or manga (tokens.Medium.Anime or tokens.Medium.Manga)
    :param user   The user whose list should be grabbed. May use credentials[0].
    """
    if user is None:
        user = credentials[0]
    if medium == Anime:
        return AnimeList(user)
    elif medium == Manga:
        return MangaList(user)
    else:
        raise ValueError("Invalid medium")

# === BLOCK 3 (label=lm, source_idx=line2989_lm, name=_groups_or_na_fun) ===
def _groups_or_na_fun(regex):
    """Used in both extract_noexpand and extract_frame"""
    def _groups_or_na_fun(regex):
        match = re.search(regex, text)
        if match:
            return match.groups()
        else:
            return "NA"

# === BLOCK 4 (label=lm, source_idx=line2990_lm, name=gen_lt) ===
def gen_lt(self):
        """Generate a new LoginTicket and add it to the list of valid LT for the user"""
        new_lt = LoginTicket()
        self.login_tickets.append(new_lt)
        return new_lt

# === BLOCK 5 (label=human, source_idx=line2390_human, name=wiki_revert) ===
def wiki_revert(self, title, version):
        """Function to revert a specific wiki page (Requires login) (UNTESTED).

        Parameters:
            title (str): The title of the wiki page to update.
            version (int): The version to revert to.
        """
        params = {'title': title, 'version': version}
        return self._get('wiki/revert', params, method='PUT')

# === BLOCK 6 (label=human, source_idx=line1392_human, name=get_vmpolicy_macaddr_output_instance_id) ===
def get_vmpolicy_macaddr_output_instance_id(self, **kwargs):
        """Auto Generated Code
        """
        config = ET.Element("config")
        get_vmpolicy_macaddr = ET.Element("get_vmpolicy_macaddr")
        config = get_vmpolicy_macaddr
        output = ET.SubElement(get_vmpolicy_macaddr, "output")
        instance_id = ET.SubElement(output, "instance-id")
        instance_id.text = kwargs.pop('instance_id')

        callback = kwargs.pop('callback', self._callback)
        return callback(config)
