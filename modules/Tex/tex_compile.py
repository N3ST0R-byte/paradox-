import os

from tex_config import default_preamble

"""
Provides a single context utility to compile LaTeX code from a user and return any error message
"""


header = "\\documentclass[preview, border=5pt, 12pt]{standalone}\
          \n\\nonstopmode"

to_compile = "{header}\
    \n{preamble}\
    \n\\begin{{document}}\
    \n{source}\
    \n\\end{{document}}"


async def makeTeX(ctx, source, userid, preamble=default_preamble, colour="default", header=header):
    path = "tex/staging/{}".format(userid)
    if not os.path.exists(path):
        os.makedirs(path)

    fn = "{}/{}.tex".format(path, userid)

    with open(fn, 'w') as work:
        work.write(to_compile.format(header, preamble, source))
        work.close()

    return await ctx.run_sh("tex/texcompile.sh {} {}".format(userid, colour))


def load_into(bot):
    bot.add_to_ctx(makeTeX)
