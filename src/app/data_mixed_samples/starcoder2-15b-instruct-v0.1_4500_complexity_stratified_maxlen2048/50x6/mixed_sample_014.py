# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line624_lm, name=install) ===
def install(path, user, admin_user, admin_password, admin_email, title, url):
    """
    Run the initial setup functions for a wordpress install

    path
        path to wordpress install location

    user
        user to run the command as

    admin_user
        Username for the Administrative user for the wordpress install

    admin_password
        Initial Password for the Administrative user for the wordpress install

    admin_email
        Email for the Administrative user for the wordpress install

    title
        Title of the wordpress website for the wordpress install

    url
        Url for the wordpress install

    CLI Example:

    .. code-block:: bash

        salt '*' wordpress.install /var/www/html apache dwallace password123 \
            dwallace@example.com "Daniel's Awesome Blog" https://blog.dwallace.com
    """
    import subprocess
    import os

    if not os.path.exists(path):
        os.makedirs(path)
    os.chdir(path)
    subprocess.run(["wp", "core", "download"], check=True)
    subprocess.run(["wp", "config", "create", "--dbhost=localhost", "--dbname=wordpress",
                    "--dbuser=wordpress", "--dbpass=wordpress"], check=True)
    subprocess.run(["wp", "core", "install", "--url={}".format(url), "--title={}".format(title),
                    "--admin_user={}".format(admin_user), "--admin_password={}".format(admin_password),
                    "--admin_email={}".format(admin_email)], check=True)

# === BLOCK 2 (label=human, source_idx=line2399_human, name=get_form) ===
def get_form(self, request, obj=None, **kwargs):
        """
        Returns a Form class for use in the admin add view. This is used by
        add_view and change_view.
        """
        parent_id = request.REQUEST.get('parent_id', None)
        if parent_id:
            return FolderForm
        else:
            folder_form = super(FolderAdmin, self).get_form(
                request, obj=None, **kwargs)

            def folder_form_clean(form_obj):
                cleaned_data = form_obj.cleaned_data
                folders_with_same_name = Folder.objects.filter(
                    parent=form_obj.instance.parent,
                    name=cleaned_data['name'])
                if form_obj.instance.pk:
                    folders_with_same_name = folders_with_same_name.exclude(
                        pk=form_obj.instance.pk)
                if folders_with_same_name.exists():
                    raise ValidationError(
                        'Folder with this name already exists.')
                return cleaned_data

            # attach clean to the default form rather than defining a new form
            # class
            folder_form.clean = folder_form_clean
            return folder_form

# === BLOCK 3 (label=lm, source_idx=line1061_lm, name=_apply_key_type) ===
def _apply_key_type(self, keys):
        """
        If a type is specified by the corresponding key dimension,
        this method applies the type to the supplied key.
        """
        for i, key in enumerate(keys):
            if self.key_types[i] is not None:
                keys[i] = self.key_types[i](key)
        return keys

# === BLOCK 4 (label=human, source_idx=line4125_human, name=save_gui_settings) ===
def save_gui_settings(self, *a):
        """
        Saves just the current configuration of the controls if the
        autosettings_path is set.
        """

        # only if we're supposed to!
        if self._autosettings_path:

            # Get the gui settings directory
            gui_settings_dir = _os.path.join(_cwd, 'egg_settings')

            # make sure the directory exists
            if not _os.path.exists(gui_settings_dir): _os.mkdir(gui_settings_dir)

            # make a path with a sub-directory
            path = _os.path.join(gui_settings_dir, self._autosettings_path)

            # for saving header info
            d = _d.databox()

            # add all the controls settings
            for x in self._autosettings_controls: self._store_gui_setting(d, x)

            # save the file
            d.save_file(path, force_overwrite=True)

# === BLOCK 5 (label=lm, source_idx=line4974_lm, name=dependents_of_addresses) ===
def dependents_of_addresses(self, addresses):
    """Given an iterable of addresses, yield all of those addresses dependents."""
    for address in addresses:
        yield from self.dependents_of_address(address)

# === BLOCK 6 (label=human, source_idx=line4009_human, name=index_normalize) ===
def index_normalize(index_val):
    """Normalize dictionary calculated key

    When parsing, keys within a dictionary may come from the input text. To ensure there is no
    space or other special caracters, one should use this function. This is useful because
    DictExt dictionaries can be access with a dotted notation that only supports ``A-Za-z0-9_`` chars.

    Args:
        index_val (str): The candidate string to a dictionary key.

    Returns:
        str: A normalized string with only ``A-Za-z0-9_`` chars

    Examples:
        >>> index_normalize('this my key')
        'this_my_key'
        >>> index_normalize('this -my- %key%')
        'this_my_key'

    """
    index_val = index_val.lower().strip()
    index_val = re.sub(r'^\W*','',index_val)
    index_val = re.sub(r'\W*$','',index_val)
    index_val = re.sub(r'\W+','_',index_val)
    index_val = re.sub('_+','_',index_val)
    return index_val
