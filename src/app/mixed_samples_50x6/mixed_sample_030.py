# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line294_lm, name=cifar_generator) ===
def cifar_generator(cifar_version, tmp_dir, training, how_many, start_from=0):
  """Image generator for CIFAR-10 and 100.

  Args:
    cifar_version: string; one of "cifar10" or "cifar100"
    tmp_dir: path to temporary storage directory.
    training: a Boolean; if true, we use the train set, otherwise the test set.
    how_many: how many images and labels to generate.
    start_from: from which image to start.

  Returns:
    An instance of image_generator that produces CIFAR-10 images and labels.
  """
  def cifar_generator(cifar_version, tmp_dir, training, how_many, start_from=0):
      if cifar_version not in ("cifar10", "cifar100"):
          raise ValueError("cifar_version must be either 'cifar10' or 'cifar100'")
      if not os.path.isdir(tmp_dir):
          raise ValueError("tmp_dir must be a valid directory")
      if how_many <= 0:
          raise ValueError("how_many must be a positive integer")
      if start_from < 0:
          raise ValueError("start_from must be a non-negative integer")
      if cifar_version == "cifar10":
          num_classes = 10
      else:
          num_classes = 100
      class image_generator:
          def __init__(self, training, how_many, start_from):
              self.training = training
              self.how_many = how_many
              self.start_from = start_from

          def __iter__(self):
              if self.training:
                  file_name = "data_batch"
              else:
                  file_name = "test_batch"
              file_path = os.path.join(tmp_dir, file_name)
              with open(file_path, "rb") as f:
                  data = pickle.load(f, encoding="bytes")
              images = data[b"data"]
              labels = data[b"labels"]
              num_images = len(images)
              for i in range(self.start_from, num_images):
                  image = images[i].reshape((3, 32, 32)).transpose(1, 2, 0)
                  label = labels[i]
                  one_hot_label = np.zeros(num_classes)
                  one_hot_label[label] = 1
                  yield image, one_hot_label

      return image_generator(training, how_many, start_from)

# === BLOCK 2 (label=human, source_idx=line294_human, name=cifar_generator) ===
def cifar_generator(cifar_version, tmp_dir, training, how_many, start_from=0):
  """Image generator for CIFAR-10 and 100.

  Args:
    cifar_version: string; one of "cifar10" or "cifar100"
    tmp_dir: path to temporary storage directory.
    training: a Boolean; if true, we use the train set, otherwise the test set.
    how_many: how many images and labels to generate.
    start_from: from which image to start.

  Returns:
    An instance of image_generator that produces CIFAR-10 images and labels.
  """
  if cifar_version == "cifar10":
    url = _CIFAR10_URL
    train_files = _CIFAR10_TRAIN_FILES
    test_files = _CIFAR10_TEST_FILES
    prefix = _CIFAR10_PREFIX
    image_size = _CIFAR10_IMAGE_SIZE
    label_key = "labels"
  elif cifar_version == "cifar100" or cifar_version == "cifar20":
    url = _CIFAR100_URL
    train_files = _CIFAR100_TRAIN_FILES
    test_files = _CIFAR100_TEST_FILES
    prefix = _CIFAR100_PREFIX
    image_size = _CIFAR100_IMAGE_SIZE
    if cifar_version == "cifar100":
      label_key = "fine_labels"
    else:
      label_key = "coarse_labels"

  _get_cifar(tmp_dir, url)
  data_files = train_files if training else test_files
  all_images, all_labels = [], []
  for filename in data_files:
    path = os.path.join(tmp_dir, prefix, filename)
    with tf.gfile.Open(path, "rb") as f:
      if six.PY2:
        data = cPickle.load(f)
      else:
        data = cPickle.load(f, encoding="latin1")
    images = data["data"]
    num_images = images.shape[0]
    images = images.reshape((num_images, 3, image_size, image_size))
    all_images.extend([
        np.squeeze(images[j]).transpose((1, 2, 0)) for j in range(num_images)
    ])
    labels = data[label_key]
    all_labels.extend([labels[j] for j in range(num_images)])
  return image_utils.image_generator(
      all_images[start_from:start_from + how_many],
      all_labels[start_from:start_from + how_many])

# === BLOCK 3 (label=lm, source_idx=line1124_lm, name=p_declare_list) ===
def p_declare_list(p):
    """declare_list : STRING EQUALS static_scalar
                    | declare_list COMMA STRING EQUALS static_scalar"""
    if len(p) == 4:
        return [(p[1], p[3])]
    else:
        return p[1] + [(p[3], p[5])]

# === BLOCK 4 (label=lm, source_idx=line315_lm, name=rate) ===
def rate(self):
        """Returns the rate of the progress as a float. Selects the unstable rate if eta_every > 1 for performance."""
        if self.eta_every > 1:
            return self.unstable_rate
        else:
            return self.stable_rate

# === BLOCK 5 (label=human, source_idx=line1816_human, name=reorder) ===
def reorder(self, index, direction):
        """
        Reorders the data being displayed in this tree.  It will check to
        see if a server side requery needs to happen based on the paging
        information for this tree.

        :param      index     | <column>
                    direction | <Qt.SortOrder>

        :sa         setOrder
        """
        columnTitle = self.columnOf(index)
        columnName  = self.columnOrderName(columnTitle)

        if not columnName:
            return

        # grab the table and ensure we have a valid column
        table = self.tableType()
        if not table:
            return

        column = table.schema().column(columnName)
        if not column:
            return

        if direction == Qt.AscendingOrder:
            db_dir = 'asc'
        else:
            db_dir = 'desc'

        order = [(columnName, db_dir)]

        # lookup reference column ordering
        if column.isReference():
            ref = column.referenceModel()
            if ref:
                ref_order = ref.schema().defaultOrder()
                if ref_order:
                    order = [(columnName + '.' + ref_order[0][0], db_dir)]
                    order += ref_order[1:]

        # update the information
        self.clear()
        super(XOrbTreeWidget, self).sortByColumn(index, direction)

        self.setOrder(order)
        self.refresh()

# === BLOCK 6 (label=human, source_idx=line374_human, name=git_status_all_repos) ===
def git_status_all_repos(cat, hard=True, origin=False, clean=True):
    """Perform a 'git status' in each data repository.
    """
    log = cat.log
    log.debug("gitter.git_status_all_repos()")

    all_repos = cat.PATHS.get_all_repo_folders()
    for repo_name in all_repos:
        log.info("Repo in: '{}'".format(repo_name))
        # Get the initial git SHA
        sha_beg = get_sha(repo_name)
        log.debug("Current SHA: '{}'".format(sha_beg))

        log.info("Fetching")
        fetch(repo_name, log=cat.log)

        git_comm = ["git", "status"]
        _call_command_in_repo(
            git_comm, repo_name, cat.log, fail=True, log_flag=True)

        sha_end = get_sha(repo_name)
        if sha_end != sha_beg:
            log.info("Updated SHA: '{}'".format(sha_end))

    return
