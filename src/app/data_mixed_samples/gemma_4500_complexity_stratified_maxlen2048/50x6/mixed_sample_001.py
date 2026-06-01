# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3565_human, name=_dict_raise_on_duplicates) ===
def _dict_raise_on_duplicates(ordered_pairs):
    """
    Reject duplicate keys.
    """
    d = {}
    for k, v in ordered_pairs:
        if k in d:
           raise ValueError("duplicate key: %r" % (k,))
        else:
           d[k] = v
    return d

# === BLOCK 2 (label=human, source_idx=line7676_human, name=_mkpart) ===
def _mkpart(root, fs_format, fs_opts, mount_dir):
    """
    Make a partition, and make it bootable

    .. versionadded:: Beryllium
    """
    __salt__['partition.mklabel'](root, 'msdos')
    loop1 = __salt__['cmd.run']('losetup -f')
    log.debug('First loop device is %s', loop1)
    __salt__['cmd.run']('losetup {0} {1}'.format(loop1, root))
    part_info = __salt__['partition.list'](loop1)
    start = six.text_type(2048 * 2048) + 'B'
    end = part_info['info']['size']
    __salt__['partition.mkpart'](loop1, 'primary', start=start, end=end)
    __salt__['partition.set'](loop1, '1', 'boot', 'on')
    part_info = __salt__['partition.list'](loop1)
    loop2 = __salt__['cmd.run']('losetup -f')
    log.debug('Second loop device is %s', loop2)
    start = start.rstrip('B')
    __salt__['cmd.run']('losetup -o {0} {1} {2}'.format(start, loop2, loop1))
    _mkfs(loop2, fs_format, fs_opts)
    __salt__['mount.mount'](mount_dir, loop2)
    __salt__['cmd.run']((
        'grub-install',
        '--target=i386-pc',
        '--debug',
        '--no-floppy',
        '--modules=part_msdos linux',
        '--boot-directory={0}/boot'.format(mount_dir),
        loop1
    ), python_shell=False)
    __salt__['mount.umount'](mount_dir)
    __salt__['cmd.run']('losetup -d {0}'.format(loop2))
    __salt__['cmd.run']('losetup -d {0}'.format(loop1))
    return part_info

# === BLOCK 3 (label=human, source_idx=line1264_human, name=run_strelka_with_merge) ===
def run_strelka_with_merge(job, tumor_bam, normal_bam, univ_options, strelka_options):
    """
    A wrapper for the the entire strelka sub-graph.

    :param dict tumor_bam: Dict of bam and bai for tumor DNA-Seq
    :param dict normal_bam: Dict of bam and bai for normal DNA-Seq
    :param dict univ_options: Dict of universal options used by almost all tools
    :param dict strelka_options: Options specific to strelka
    :return: fsID to the merged strelka calls
    :rtype: toil.fileStore.FileID
    """
    spawn = job.wrapJobFn(run_strelka, tumor_bam, normal_bam, univ_options,
                          strelka_options, split=False).encapsulate()
    job.addChild(spawn)
    return spawn.rv()

# === BLOCK 4 (label=human, source_idx=line685_human, name=FoldByteStream) ===
def FoldByteStream(self, mapped_value, context=None, **unused_kwargs):
    """Folds the data type into a byte stream.

    Args:
      mapped_value (object): mapped value.
      context (Optional[DataTypeMapContext]): data type map context.

    Returns:
      bytes: byte stream.

    Raises:
      FoldingError: if the data type definition cannot be folded into
          the byte stream.
    """
    elements_data_size = self._CalculateElementsDataSize(context)
    if elements_data_size is not None:
      if elements_data_size != len(mapped_value):
        raise errors.FoldingError(
            'Mismatch between elements data size and mapped value size')

    elif not self._HasElementsTerminator():
      raise errors.FoldingError('Unable to determine elements data size')

    else:
      elements_terminator = self._data_type_definition.elements_terminator
      elements_terminator_size = len(elements_terminator)
      if mapped_value[-elements_terminator_size:] != elements_terminator:
        mapped_value = b''.join([mapped_value, elements_terminator])

    return mapped_value

# === BLOCK 5 (label=human, source_idx=line33_human, name=parse) ===
def parse(text):
        """Try to parse into a date.

        Return:
            tuple (year, month, date) if successful; otherwise None.
        """
        try:
            ymd = text.lower().split('-')
            assert len(ymd) == 3
            year = -1 if ymd[0] in ('xx', 'xxxx') else int(ymd[0])
            month = -1 if ymd[1] == 'xx' else int(ymd[1])
            day = -1 if ymd[2] == 'xx' else int(ymd[2])
            assert not year == month == day == -1
            assert month == -1 or 1 <= month <= 12
            assert day == -1 or 1 <= day <= 31
            return (year, month, day)
        except (ValueError, AssertionError):
            return None

# === BLOCK 6 (label=human, source_idx=line2086_human, name=insertFromMimeData) ===
def insertFromMimeData(self, source):
        """
        Inserts the information from the inputed source.

        :param      source | <QMimeData>
        """
        lines = projex.text.nativestring(source.text()).splitlines()
        for i in range(1, len(lines)):
            if not lines[i].startswith('... '):
                lines[i] = '... ' + lines[i]

        if len(lines) > 1:
            lines.append('... ')

        self.insertPlainText('\n'.join(lines))
