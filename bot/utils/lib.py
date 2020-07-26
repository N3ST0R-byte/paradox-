import datetime

# from logger import log


def prop_tabulate(prop_list, value_list):
    """
    Turns a list of properties and corresponding list of values into
    a pretty string with one `prop: value` pair each line,
    padded so that the colons in each line are lined up.
    Handles empty props by using an extra couple of spaces instead of a `:`.

    Parameters
    ----------
    prop_list: List[str]
        List of short names to put on the right side of the list.
        Empty props are considered to be "newlines" for the corresponding value.
    value_list: List[str]
        List of values corresponding to the properties above.

    Returns: str
    """
    max_len = max(len(prop) for prop in prop_list)
    return "\n".join(["`{}{}{}`\t{}".format("​ " * (max_len - len(prop)),
                                            prop,
                                            ":" if len(prop) > 1 else "​ " * 2,
                                            value_list[i]) for i, prop in enumerate(prop_list)])


def paginate_list(item_list, block_length=20, style="markdown", title=None):
    """
    Create pretty codeblock pages from a list of strings.

    Parameters
    ----------
    item_list: List[str]
        List of strings to paginate.
    block_length: int
        Maximum number of strings per page.
    style: str
        Codeblock style to use.
        Title formatting assumes the `markdown` style, and numbered lists work well with this.
        However, `markdown` sometimes messes up formatting in the list.
    title: str
        Optional title to add to the top of each page.

    Returns: List[str]
        List of pages, each formatted into a codeblock,
        and containing at most `block_length` of the provided strings.
    """
    lines = ["{0:<5}{1:<5}".format("{}.".format(i + 1), str(line)) for i, line in enumerate(item_list)]
    page_blocks = [lines[i:i + block_length] for i in range(0, len(lines), block_length)]
    pages = []
    for i, block in enumerate(page_blocks):
        pagenum = "Page {}/{}".format(i + 1, len(page_blocks))
        if title:
            header = "{} ({})".format(title, pagenum) if len(page_blocks) > 1 else title
        else:
            header = pagenum
        header_line = "=" * len(header)
        full_header = "{}\n{}\n".format(header, header_line) if len(page_blocks) > 1 or title else ""
        pages.append("```{}\n{}{}```".format(style, full_header, "\n".join(block)))
    return pages


def timestamp_utcnow():
    """
    Return the current integer UTC timestamp.
    """
    return int(datetime.datetime.timestamp(datetime.datetime.utcnow()))


def split_text(text, blocksize=2000, code=True, syntax="", maxheight=50):
    """
    Break the text into blocks of maximum length blocksize
    If possible, break across nearby newlines. Otherwise just break at blocksize chars

    Parameters
    ----------
    text: str
        Text to break into blocks.
    blocksize: int
        Maximum character length for each block.
    code: bool
        Whether to wrap each block in codeblocks (these are counted in the blocksize).
    syntax: str
        The markdown formatting language to use for the codeblocks, if applicable.
    maxheight: int
        The maximum number of lines in each block

    Returns: List[str]
        List of blocks,
        each containing at most `block_size` characters,
        of height at most `maxheight`.
    """
    # Adjust blocksize to account for the codeblocks if required
    blocksize = blocksize - 8 - len(syntax) if code else blocksize

    # Build the blocks
    blocks = []
    while True:
        # If the remaining text is already small enough, append it
        if len(text) <= blocksize:
            blocks.append(text)
            break

        # Find the last newline in the prototype block
        split_on = text[0:blocksize].rfind('\n')
        split_on = blocksize if split_on == -1 else split_on

        # Add the block and truncate the text
        blocks.append(text[0:split_on])
        text = text[split_on:]

    # Add the codeblock ticks and the code syntax header, if required
    if code:
        blocks = ["```{}\n{}\n```".format(syntax, block) for block in blocks]

    return blocks


def strfdelta(delta, sec=False, minutes=True, short=False):
    """
    Convert a datetime.timedelta object into an easily readable duration string.

    Parameters
    ----------
    delta: datetime.timedelta
        The timedelta object to convert into a readable string.
    sec: bool
        Whether to include the seconds from the timedelta object in the string.
    minutes: bool
        Whether to include the minutes from the timedelta object in the string.
    short: bool
        Whether to abbreviate the units of time ("hour" to "h", "minute" to "m", "second" to "s").

    Returns: str
        A string containing a time from the datetime.timedelta object, in a readable format.
        Time units will be abbreviated if short was set to True.
    """

    output = [[delta.days, 'd' if short else ' day'],
              [delta.seconds // 3600, 'h' if short else ' hour']]
    if minutes:
        output.append([delta.seconds // 60 % 60, 'm' if short else ' minute'])
    if sec:
        output.append([delta.seconds % 60, 's' if short else ' second'])
    for i in range(len(output)):
        if output[i][0] != 1 and not short:
            output[i][1] += 's'
    reply_msg = []
    if output[0][0] != 0:
        reply_msg.append("{}{} ".format(output[0][0], output[0][1]))
    for i in range(1, len(output) - 1):
        reply_msg.append("{}{} ".format(output[i][0], output[i][1]))
    if not short and reply_msg:
        reply_msg.append("and ")
        reply_msg.append("{}{}".format(output[len(output) - 1][0], output[len(output) - 1][1]))
        return "".join(reply_msg)


def parse_dur(time_str):
    """
    Parses a user provided time duration string into a timedelta object.

    Parameters
    ----------
    time_str: str
        The time string to parse. String can include days, hours, minutes, and seconds.

    Returns: str
        A string with a formatted timedelta object.
    """
    funcs = {'d': lambda x: x * 24 * 60 * 60,
             'h': lambda x: x * 60 * 60,
             'm': lambda x: x * 60,
             's': lambda x: x}
    time_str = time_str.strip(" ,")
    found = re.findall(r'(\d+)\s?(\w+?)', time_str)
    seconds = 0
    for bit in found:
        if bit[1] in funcs:
            seconds += funcs[bit[1]](int(bit[0]))
    return datetime.timedelta(seconds=seconds)
