# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line5732_lm, name=toggle_rich_text) ===
def toggle_rich_text(self, checked):
        """Toggle between sphinxified docstrings or plain ones"""
        self.rich_text = checked
        self.update_text()

# === BLOCK 2 (label=human, source_idx=line2384_human, name=process_result_value) ===
def process_result_value(self, value: Optional[str],
                             dialect: Dialect) -> List[int]:
        """Convert things on the way from the database to Python."""
        retval = self._dbstr_to_intlist(value)
        return retval

# === BLOCK 3 (label=human, source_idx=line810_human, name=_StartWorkerProcess) ===
def _StartWorkerProcess(self, process_name, storage_writer):
    """Creates, starts, monitors and registers a worker process.

    Args:
      process_name (str): process name.
      storage_writer (StorageWriter): storage writer for a session storage used
          to create task storage.

    Returns:
      MultiProcessWorkerProcess: extraction worker process or None if the
          process could not be started.
    """
    process_name = 'Worker_{0:02d}'.format(self._last_worker_number)
    logger.debug('Starting worker process {0:s}'.format(process_name))

    if self._use_zeromq:
      queue_name = '{0:s} task queue'.format(process_name)
      task_queue = zeromq_queue.ZeroMQRequestConnectQueue(
          delay_open=True, linger_seconds=0, name=queue_name,
          port=self._task_queue_port,
          timeout_seconds=self._TASK_QUEUE_TIMEOUT_SECONDS)
    else:
      task_queue = self._task_queue

    process = worker_process.WorkerProcess(
        task_queue, storage_writer, self._artifacts_filter_helper,
        self.knowledge_base, self._session_identifier,
        self._processing_configuration,
        enable_sigsegv_handler=self._enable_sigsegv_handler, name=process_name)

    # Remove all possible log handlers to prevent a child process from logging
    # to the main process log file and garbling the log. The log handlers are
    # recreated after the worker process has been started.
    for handler in logging.root.handlers:
      logging.root.removeHandler(handler)
      handler.close()

    process.start()

    loggers.ConfigureLogging(
        debug_output=self._debug_output, filename=self._log_filename,
        mode='a', quiet_mode=self._quiet_mode)

    try:
      self._StartMonitoringProcess(process)

    except (IOError, KeyError) as exception:
      pid = process.pid
      logger.error((
          'Unable to monitor replacement worker process: {0:s} '
          '(PID: {1:d}) with error: {2!s}').format(
              process_name, pid, exception))

      self._TerminateProcess(process)
      return None

    self._RegisterProcess(process)

    self._last_worker_number += 1

    return process

# === BLOCK 4 (label=lm, source_idx=line4440_lm, name=moduleInfo) ===
def moduleInfo( module ):
        """
        Generates HTML information to display for the about info for a module.

        :param      module  | <module>
        """
        # Get the module's name
        moduleName = module.__name__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's description
        moduleDescription = module.__doc__

        # Get the module's author
        moduleAuthor = module.__author__

        # Get the module's email
        moduleEmail = module.__email__

        # Get the module's url
        moduleUrl = module.__url__

        # Get the module's license
        moduleLicense = module.__license__

        # Get the module's copyright
        moduleCopyright = module.__copyright__

        # Get the module's date
        moduleDate = module.__date__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get the module's version
        moduleVersion = module.__version__

        # Get

# === BLOCK 5 (label=lm, source_idx=line6480_lm, name=detectRamPorts) ===
def detectRamPorts(stm: IfContainer, current_en: RtlSignalBase):
    """
    Detect RAM ports in If statement

    :param stm: statement to detect the ram ports in
    :param current_en: curent en/clk signal
    """
    if isinstance(stm, IfContainer):
        if isinstance(stm.condition, RtlSignalBase):
            if stm.condition.name == current_en.name:
                if isinstance(stm.then_stm, IfContainer):
                    detectRamPorts(stm.then_stm, current_en)
                elif isinstance(stm.else_stm, IfContainer):
                    detectRamPorts(stm.else_stm, current_en)
                else:
                    raise Exception("Unknown If statement")
            else:
                raise Exception("Unknown If statement")
        else:
            raise Exception("Unknown If statement")
    else:
        raise Exception("Unknown If statement")

# === BLOCK 6 (label=human, source_idx=line5952_human, name=from_dict) ===
def from_dict(cls, d):
        """
        Returns an IonEntry object from a dict.
        """
        return IonEntry(Ion.from_dict(d["ion"]), d["energy"], d.get("name", None))
