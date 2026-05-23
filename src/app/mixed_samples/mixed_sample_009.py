# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1832_lm, name=bin_data_format) ===
def bin_data_format(self):
        """
        Returns the format of the values in `bin_data` for the current mode.
        Possible values are:

        - `u8`: Unsigned 8-bit integer (byte)
        - `s8`: Signed 8-bit integer (sbyte)
        - `u16`: Unsigned 16-bit integer (ushort)
        - `s16`: Signed 16-bit integer (short)
        - `s16_be`: Signed 16-bit integer, big endian
        - `s32`: Signed 32-bit integer (int)
        - `float`: IEEE 754 32-bit floating point (float)
        """
        if self.mode == "u8":
            return "u8"
        elif self.mode == "s8":
            return "s8"
        elif self.mode == "u16":
            return "u16"
        elif self.mode == "s16":
            return "s16"
        elif self.mode == "s16_be":
            return "s16_be"
        elif self.mode == "s32":
            return "s32"
        elif self.mode == "float":
            return "float"
        else:
            raise ValueError("Invalid mode")

# === BLOCK 2 (label=lm, source_idx=line2769_lm, name=is_result_edition_allowed) ===
def is_result_edition_allowed(self, analysis_brain):
        """Checks if the edition of the result field is allowed

        :param analysis_brain: Brain that represents an analysis
        :return: True if the user can edit the result field, otherwise False
        """
        if self.user.is_admin or self.user.is_owner(analysis_brain):
            return True
        if self.user.is_collaborator(analysis_brain):
            return analysis_brain.result_edition_allowed
        return False

# === BLOCK 3 (label=lm, source_idx=line542_lm, name=folderitem) ===
def folderitem(self, obj, item, index):
        """Applies new properties to the item (Client) that is currently being
        rendered as a row in the list

        :param obj: client to be rendered as a row in the list
        :param item: dict representation of the client, suitable for the list
        :param index: current position of the item within the list
        :type obj: ATContentType/DexterityContentType
        :type item: dict
        :type index: int
        :return: the dict representation of the item
        :rtype: dict
        """
        item['id'] = obj.id
        item['title'] = obj.title
        item['description'] = obj.description
        item['review_state'] = obj.review_state
        item['url'] = obj.absolute_url()
        item['path'] = '/'.join(obj.getPhysicalPath())
        item['icon'] = obj.getIcon()
        item['portal_type'] = obj.portal_type
        item['modified'] = obj.modified().strftime('%Y-%m-%d %H:%M')
        item['modified_time'] = obj.modified().strftime('%H:%M')
        item['created'] = obj.created().strftime('%Y-%m-%d %H:%M')
        item['created_time'] = obj.created().strftime('%H:%M')
        item['review_state_title'] = self.translate(obj.review_state)
        item['obj'] = obj
        item['index'] = index
        return item

# === BLOCK 4 (label=lm, source_idx=line1703_lm, name=set_ys) ===
def set_ys(self, word):
        """
        Identify Ys that are to be treated
        as consonants and make them uppercase.
        """
        for i in range(len(word)):
            if word[i] == 'y':
                if i == 0:
                    word = word[:i] + word[i].upper() + word[i+1:]
                elif word[i-1] not in self.vowels:
                    word = word[:i] + word[i].upper() + word[i+1:]

        return word
