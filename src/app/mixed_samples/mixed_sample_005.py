# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line549_human, name=add_arg_param) ===
def add_arg_param(self, param_name, layer_index, blob_index):
        """Add an arg param to .params file. Example: weights of a fully connected layer."""
        self.add_param('arg:%s' % param_name, layer_index, blob_index)

# === BLOCK 2 (label=lm, source_idx=line2556_lm, name=diff_safe) ===
def diff_safe(cls, value):
        """Return a value that can be safely stored as a diff"""
        if cls == int:
            return value + 1
        elif cls == float:
            return value + 0.1
        elif cls == str:
            return value + "diff"
        else:
            raise ValueError("Unsupported class")

# === BLOCK 3 (label=lm, source_idx=line2625_lm, name=user_choice) ===
def user_choice(prompt, choices=("yes", "no"), default=None):
    """
    Prompts the user for confirmation.  The default value, if any, is capitalized.

    :param prompt: Information to display to the user.
    :param choices: an iterable of possible choices.
    :param default: default choice
    :return: the user's choice
    """
    if default is not None:
        default = default.capitalize()
    print(prompt)
    if default is not None:
        print(f"[{default}]")
    choice = input("> ")
    if choice == "":
        return default
    if choice in choices:
        return choice
    else:
        raise ValueError(f"Invalid choice: {choice}")

# === BLOCK 4 (label=lm, source_idx=line2314_lm, name=extract_to_disk) ===
def extract_to_disk(self):
        """Extract all files and write them to disk."""
        for file in self.files:
            file.extract(self.output_dir)

# === BLOCK 5 (label=lm, source_idx=line2247_lm, name=calc_gradev_phase) ===
def calc_gradev_phase(data, rate, mj, stride, confidence, noisetype):
    """ see http://www.leapsecond.com/tools/adev_lib.c
        stride = mj for nonoverlapping allan deviation
        stride = 1 for overlapping allan deviation

        see http://en.wikipedia.org/wiki/Allan_variance
             1       1
         s2y(t) = --------- sum [x(i+2) - 2x(i+1) + x(i) ]^2
                  2*tau^2
    """
    n = len(data)
    s2y = []
    for tau in range(1, n // 2):
        sum_squared_diff = 0
        for i in range(0, n - 2 * tau, stride):
            sum_squared_diff += (data[i + 2 * tau] - 2 * data[i + tau] + data[i]) ** 2
        s2y.append(sum_squared_diff / (2 * tau ** 2))
    return s2y
