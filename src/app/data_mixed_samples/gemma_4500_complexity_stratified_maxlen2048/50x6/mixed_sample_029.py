# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line163_human, name=get_desktop_for_window) ===
def get_desktop_for_window(self, window):
        """
        Get the desktop a window is on.
        Uses _NET_WM_DESKTOP of the EWMH spec.

        If your desktop does not support ``_NET_WM_DESKTOP``, then '*desktop'
        remains unmodified.

        :param wid: the window to query
        """
        desktop = ctypes.c_long(0)
        _libxdo.xdo_get_desktop_for_window(
            self._xdo, window, ctypes.byref(desktop))
        return desktop.value

# === BLOCK 2 (label=lm, source_idx=line1706_lm, name=pad_to_same_length) ===
def pad_to_same_length(x, y, final_length_divisible_by=1, axis=1):
  """Pad tensors x and y on axis 1 so that they have the same length."""
  import torch.nn.functional as F
  import torch

  max_len = max(x.shape[axis], y.shape[axis])
  if final_length_divisible_by > 1:
      max_len = ((max_len + final_length_divisible_by - 1) // final_length_divisible_by) * final_length_divisible_by

  def get_padding(tensor):
      current_len = tensor.shape[axis]
      pad_total = max_len - current_len
      # F.pad expects padding from last dimension backwards
      # We need to construct a padding list for all dimensions
      padding = [0] * (2 * tensor.ndim)
      # Index for the specific axis from the end
      axis_idx_from_end = tensor.ndim - 1 - axis
      # F.pad uses (left, right, top, bottom, ...)
      # For the target axis, we pad only on the right (end)
      padding[2 * axis_idx_from_end + 1] = pad_total
      return padding

  x_padded = F.pad(x, get_padding(x))
  y_padded = F.pad(y, get_padding(y))
  return x_padded, y_padded

# === BLOCK 3 (label=human, source_idx=line7546_human, name=_invoke_callbacks) ===
def _invoke_callbacks(self):
        """Record the task_end_time & task_cost_time, set result for self._callback_result."""
        self.task_end_time = time.time()
        self.task_cost_time = self.task_end_time - self.task_start_time
        with self._condition:
            for callback in self._done_callbacks:
                try:
                    result = callback(self)
                    if callback in self._user_callbacks:
                        self._callback_result = result
                except Exception as e:
                    Config.main_logger.error("exception calling callback for %s" % e)
            self._condition.notify_all()

# === BLOCK 4 (label=lm, source_idx=line7171_lm, name=open) ===
def open(filename, frame='unspecified'):
        """Creates a DepthImage from a file.

        Parameters
        ----------
        filename : :obj:`str`
            The file to load the data from. Must be one of .png, .jpg,
            .npy, or .npz.

        frame : :obj:`str`
            A string representing the frame of reference in which the new image
            lies.

        Returns
        -------
        :obj:`DepthImage`
            The new depth image.
        """
        import numpy as np
        from PIL import Image
        import os

        ext = os.path.splitext(filename)[1].lower()
        if ext in ('.png', '.jpg', '.jpeg'):
            data = np.array(Image.open(filename)).astype(np.float32)
        elif ext == '.npy':
            data = np.load(filename)
        elif ext == '.npz':
            with np.load(filename) as loaded:
                data = loaded[loaded.files[0]]
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

        return DepthImage(data, frame=frame)

# === BLOCK 5 (label=lm, source_idx=line4671_lm, name=delete_role) ===
def delete_role(self, name):
        # type: (str) -> None
        """Delete a role by first deleting all inline policies."""
        role = self.iam.get_role(Name=name)
        inline_policies = self.iam.list_role_policies(RoleName=name)['PolicyNames']
        for policy_name in inline_policies:
            self.iam.delete_role_policy(RoleName=name, PolicyName=policy_name)
        self.iam.delete_role(RoleName=name)

# === BLOCK 6 (label=human, source_idx=line3366_human, name=is_uri_to_be_filtered) ===
def is_uri_to_be_filtered(uri, filter_list):
    """Test whether @uri should be filtered by @filter_list."""
    match = False
    if filter_list:
        for uri_filter in filter_list:
            if re.search(uri_filter, uri, flags=re.IGNORECASE):
                match = True
        return match
