# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line7531_lm, name=create_exchange) ===
def create_exchange(self):
        """
        Creates MQ exchange for this channel
        Needs to be defined only once.
        """
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type=self.exchange_type,
            durable=self.durable
        )

# === BLOCK 2 (label=lm, source_idx=line1927_lm, name=random_word) ===
def random_word(tokens, tokenizer):
    """
    Masking some random tokens for Language Model task with probabilities as in the original BERT paper.
    :param tokens: list of str, tokenized sentence.
    :param tokenizer: Tokenizer, object used for tokenization (we need it's vocab here)
    :return: (list of str, list of int), masked tokens and related labels for LM prediction
    """
    import random

    vocab = tokenizer.vocab
    masked_tokens = []
    labels = []

    for token in tokens:
        prob = random.random()
        if prob < 0.15:
            # 80% of the time, replace with [MASK]
            if random.random() < 0.8:
                masked_tokens.append(tokenizer.mask_token)
            # 10% of the time, replace with a random token
            elif random.random() < 0.5:
                masked_tokens.append(random.choice(list(vocab.keys())))
            # 10% of the time, keep the token as is
            else:
                masked_tokens.append(token)

            labels.append(vocab.get(token, vocab.get(tokenizer.unk_token)))
        else:
            masked_tokens.append(token)
            labels.append(-1) # Use -1 or a specific ignore_index for non-masked tokens

    return masked_tokens, labels

# === BLOCK 3 (label=human, source_idx=line1150_human, name=scale_image) ===
def scale_image(image, new_width):
    """Resizes an image preserving the aspect ratio.
    """
    (original_width, original_height) = image.size
    aspect_ratio = original_height/float(original_width)
    new_height = int(aspect_ratio * new_width)

    # This scales it wider than tall, since characters are biased
    new_image = image.resize((new_width*2, new_height))
    return new_image

# === BLOCK 4 (label=human, source_idx=line8132_human, name=copy_data) ===
def copy_data(from_client, from_project, from_logstore, from_time, to_time=None,
              to_client=None, to_project=None, to_logstore=None,
              shard_list=None,
              batch_size=None, compress=None, new_topic=None, new_source=None):
    """
    copy data from one logstore to another one (could be the same or in different region), the time is log received time on server side.

    """
    to_client = to_client or from_client
    # increase the timeout to 2 min at least
    from_client.timeout = max(from_client.timeout, 120)
    to_client.timeout = max(to_client.timeout, 120)

    to_project = to_project or from_project
    to_logstore = to_logstore or from_logstore
    to_time = to_time or "end"

    cpu_count = multiprocessing.cpu_count() * 2
    shards = from_client.list_shards(from_project, from_logstore).get_shards_info()
    current_shards = [str(shard['shardID']) for shard in shards]
    target_shards = _parse_shard_list(shard_list, current_shards)
    worker_size = min(cpu_count, len(target_shards))

    result = dict()
    total_count = 0
    with ProcessPoolExecutor(max_workers=worker_size) as pool:
        futures = [pool.submit(copy_worker, from_client, from_project, from_logstore, shard,
                               from_time, to_time,
                               to_client, to_project, to_logstore,
                               batch_size=batch_size, compress=compress,
                               new_topic=new_topic, new_source=new_source)
                   for shard in target_shards]

        for future in as_completed(futures):
            partition, count = future.result()
            total_count += count
            if count:
                result[partition] = count

    return LogResponse({}, {"total_count": total_count, "shards": result})

# === BLOCK 5 (label=human, source_idx=line6225_human, name=enable_global_typechecked_decorator) ===
def enable_global_typechecked_decorator(flag = True, retrospective = True):
    """Enables or disables global typechecking mode via decorators.
    See flag global_typechecked_decorator.
    In contrast to setting the flag directly, this function provides
    a retrospective option. If retrospective is true, this will also
    affect already imported modules, not only future imports.
    Does not work if checking_enabled is false.
    Does not work reliably if checking_enabled has ever been set to
    false during current run.
    """
    global global_typechecked_decorator
    global_typechecked_decorator = flag
    if import_hook_enabled:
        _install_import_hook()
    if global_typechecked_decorator and retrospective:
        _catch_up_global_typechecked_decorator()
    return global_typechecked_decorator

# === BLOCK 6 (label=lm, source_idx=line2245_lm, name=Compile) ===
def Compile(self, filter_implemention):
    """Compile the binary expression into a filter object."""
    return compile(filter_implemention, '<filter>', 'eval')
