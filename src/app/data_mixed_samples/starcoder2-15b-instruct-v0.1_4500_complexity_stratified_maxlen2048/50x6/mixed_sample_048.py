# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3200_human, name=_format_background) ===
def _format_background(background):
    """Formats the background section

    :param background: the background content or file.

    :type background: str or file

    :returns: the background content.
    :rtype: str

    """
    # Getting the background
    if os.path.isfile(background):
        with open(background, "r") as i_file:
            background = i_file.read().splitlines()
    else:
        background = background.splitlines()

    # Formatting
    final_background = ""
    for line in background:
        if line == "":
            final_background += r"\\" + "\n\n"
            continue

        final_background += latex.wrap_lines(latex.sanitize_tex(line))

    return final_background

# === BLOCK 2 (label=human, source_idx=line3320_human, name=get_resource_type_from_included_serializer) ===
def get_resource_type_from_included_serializer(self):
        """
        Check to see it this resource has a different resource_name when
        included and return that name, or None
        """
        field_name = self.field_name or self.parent.field_name
        parent = self.get_parent_serializer()

        if parent is not None:
            # accept both singular and plural versions of field_name
            field_names = [
                inflection.singularize(field_name),
                inflection.pluralize(field_name)
            ]
            includes = get_included_serializers(parent)
            for field in field_names:
                if field in includes.keys():
                    return get_resource_type_from_serializer(includes[field])

        return None

# === BLOCK 3 (label=human, source_idx=line2518_human, name=help) ===
def help(cls, task=None):
        """Describe available tasks or one specific task"""
        if task is None:
            usage_list = []
            for task in iter(cls._tasks):
                task_func = getattr(cls, task)
                usage_string = "  %s %s" % (cls._prog, task_func.usage)
                desc = task_func.__doc__.splitlines()[0]
                usage_list.append((usage_string, desc))
            max_len = functools.reduce(lambda m, item: max(m, len(item[0])), usage_list, 0)
            print("Tasks:")
            cols = int(os.environ.get("COLUMNS", 80))
            for line, desc in usage_list:
                task_func = getattr(cls, task)
                if desc:
                    line = "%s%s  # %s" % (line, " " * (max_len - len(line)), desc)
                if len(line) > cols:
                    line = line[:cols - 3] + "..."
                print(line)
        else:
            task_func = getattr(cls, task)
            print("Usage:")
            print("  %s %s" % (cls._prog, task_func.usage))
            print("")
            print(task_func.__doc__)

# === BLOCK 4 (label=lm, source_idx=line869_lm, name=set_default_unit_all) ===
def set_default_unit_all(self, twig=None, unit=None, **kwargs):
        """
        TODO: add documentation
        """
        if twig is None:
            for twig in self.twigs:
                self.set_default_unit(twig, unit, **kwargs)
        else:
            self.set_default_unit(twig, unit, **kwargs)

# === BLOCK 5 (label=lm, source_idx=line3600_lm, name=compute_texptime) ===
def compute_texptime(imageObjectList):
    """
    Add up the exposure time for all the members in
    the pattern, since 'drizzle' doesn't have the necessary
    information to correctly set this itself.
    """
    total_exposure_time = 0
    for image in imageObjectList:
        total_exposure_time += image.exptime
    return total_exposure_time

# === BLOCK 6 (label=lm, source_idx=line439_lm, name=start) ===
def start(self, payload):
        """Start the daemon and all processes or only specific processes."""
        if payload.get("processes"):
            for process in payload["processes"]:
                self.start_process(process)
        else:
            self.start_daemon()
