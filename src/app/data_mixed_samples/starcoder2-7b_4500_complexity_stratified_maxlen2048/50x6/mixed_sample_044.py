# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3656_human, name=find_topics) ===
def find_topics(token_lists, num_topics=10):
    """ Find the topics in a list of texts with Latent Dirichlet Allocation. """
    dictionary = Dictionary(token_lists)
    print('Number of unique words in original documents:', len(dictionary))

    dictionary.filter_extremes(no_below=2, no_above=0.7)
    print('Number of unique words after removing rare and common words:', len(dictionary))

    corpus = [dictionary.doc2bow(tokens) for tokens in token_lists]
    model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=num_topics, chunksize=100, passes=5, random_state=1)

    print_topics(model)

    return model, dictionary

# === BLOCK 2 (label=human, source_idx=line6928_human, name=get_categories) ===
def get_categories(blog_id, username, password):
    """
    metaWeblog.getCategories(blog_id, username, password)
    => category structure[]
    """
    authenticate(username, password)
    site = Site.objects.get_current()
    return [category_structure(category, site)
            for category in Category.objects.all()]

# === BLOCK 3 (label=lm, source_idx=line76_lm, name=get_basis_family) ===
def get_basis_family(basis_name, data_dir=None):
    """Lookup a family by a basis set name
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
    with open(os.path.join(data_dir, 'basis_families.json')) as f:
        basis_families = json.load(f)
    return basis_families[basis_name]

# === BLOCK 4 (label=lm, source_idx=line2488_lm, name=name) ===
def name(self):
        """ Returns the recipe name which is its class name without package. """
        return self.__class__.__name__

# === BLOCK 5 (label=lm, source_idx=line5498_lm, name=setattr_context) ===
def setattr_context(obj, **kwargs):
    """
    Context manager to temporarily change the values of object attributes
    while executing a function.

    Example
    -------
    >>> class Foo: pass
    >>> f = Foo(); f.attr = 'hello'
    >>> with setattr_context(f, attr='goodbye'):
    ...     print(f.attr)
    goodbye
    >>> print(f.attr)
    hello
    """
    old_attrs = {}
    for key, value in kwargs.items():
        old_attrs[key] = getattr(obj, key)
        setattr(obj, key, value)
    try:
        yield
    finally:
        for key, value in old_attrs.items():
            setattr(obj, key, value)

# === BLOCK 6 (label=human, source_idx=line132_human, name=runSavedQueryByUrl) ===
def runSavedQueryByUrl(self, saved_query_url, returned_properties=None):
        """Query workitems using the saved query url

        :param saved_query_url: the saved query url
        :param returned_properties: the returned properties that you want.
            Refer to :class:`rtcclient.client.RTCClient` for more explanations
        :return: a :class:`list` that contains the queried
            :class:`rtcclient.workitem.Workitem` objects
        :rtype: list
        """

        try:
            if "=" not in saved_query_url:
                raise exception.BadValue()
            saved_query_id = saved_query_url.split("=")[-1]
            if not saved_query_id:
                raise exception.BadValue()
        except:
            error_msg = "No saved query id is found in the url"
            self.log.error(error_msg)
            raise exception.BadValue(error_msg)
        return self._runSavedQuery(saved_query_id,
                                   returned_properties=returned_properties)
