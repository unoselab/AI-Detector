# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line5480_lm, name=has_map) ===
def has_map(self):
        """Return the has map attribute of the BFD file being processed."""
        return self.has_map

# === BLOCK 2 (label=human, source_idx=line6844_human, name=rss_create) ===
def rss_create(channel, articles):
    """Create RSS xml feed.

    :param channel: channel info [title, link, description, language]
    :type channel: dict(str, str)
    :param articles: list of articles, an article is a dictionary with some \
    required fields [title, description, link] and any optional, which will \
    result to `<dict_key>dict_value</dict_key>`
    :type articles: list(dict(str,str))
    :return: root element
    :rtype: ElementTree.Element
    """
    channel = channel.copy()

    # TODO use deepcopy
    # list will not clone the dictionaries in the list and `elemen_from_dict`
    # pops items from them
    articles = list(articles)

    rss = ET.Element('rss')
    rss.set('version', '2.0')

    channel_node = ET.SubElement(rss, 'channel')

    element_from_dict(channel_node, channel, 'title')
    element_from_dict(channel_node, channel, 'link')
    element_from_dict(channel_node, channel, 'description')
    element_from_dict(channel_node, channel, 'language')

    for article in articles:
        item = ET.SubElement(channel_node, 'item')

        element_from_dict(item, article, 'title')
        element_from_dict(item, article, 'description')
        element_from_dict(item, article, 'link')

        for key in article:
            complex_el_from_dict(item, article, key)

    return ET.ElementTree(rss)

# === BLOCK 3 (label=human, source_idx=line2488_human, name=name) ===
def name(self):
        """ Returns the recipe name which is its class name without package. """
        if not hasattr(self, '_name'):
            self._name = re.search('[a-z]+\.([a-z]+)\.([a-z]+)', str(self.__class__), re.IGNORECASE).group(2)

        return self._name

# === BLOCK 4 (label=human, source_idx=line2993_human, name=authorized) ===
def authorized(self, environ):
        """
        If we're running Django and ``GNOTTY_LOGIN_REQUIRED`` is set
        to ``True``, pull the session cookie from the environment and
        validate that the user is authenticated.
        """
        if self.django and settings.LOGIN_REQUIRED:
            try:
                from django.conf import settings as django_settings
                from django.contrib.auth import SESSION_KEY
                from django.contrib.auth.models import User
                from django.contrib.sessions.models import Session
                from django.core.exceptions import ObjectDoesNotExist
                cookie = SimpleCookie(environ["HTTP_COOKIE"])
                cookie_name = django_settings.SESSION_COOKIE_NAME
                session_key = cookie[cookie_name].value
                session = Session.objects.get(session_key=session_key)
                user_id = session.get_decoded().get(SESSION_KEY)
                user = User.objects.get(id=user_id)
            except (ImportError, KeyError, ObjectDoesNotExist):
                return False
        return True

# === BLOCK 5 (label=lm, source_idx=line3166_lm, name=post) ===
def post(self, param, h, r):
        """
        Args:
            param: request parameters
            h: ResultHandler
            r: YunpianApiResult
        """
        pass

# === BLOCK 6 (label=lm, source_idx=line5098_lm, name=view_task_durations) ===
def view_task_durations(token, dstore):
    """
    Display the raw task durations. Here is an example of usage::

      $ oq show task_durations:classical
    """
    # Get the task durations
    task_durations = dstore.get_task_durations(token)

    # Display the task durations
    print(task_durations)
