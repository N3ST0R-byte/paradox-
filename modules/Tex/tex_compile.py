import os

from tex_config import default_preamble


header = "\\documentclass[preview, border=5pt, 12pt]{standalone}\
          \n\\nonstopmode\
          \n\\everymath{\\displaystyle}\
          \n\\usepackage[mathletters]{ucs}\
          \n\\usepackage[utf8x]{inputenc}"


async def makeTeX(ctx, source, userid, preamble=default_preamble, colour="default", header=header):
    path = "tex/staging/{}".format(userid)
    if not os.path.exists(path):
        os.makedirs(path)

    fn = "{}/{}.tex".format(path, userid)

    with open(fn, 'w') as work:
        work.write(header + preamble)
        work.write('\n' + '\\begin{document}' + '\n')
        work.write(source)
        work.write('\n' + '\\end{document}' + '\n')
        work.close()

    return await ctx.run_sh("tex/texcompile.sh {} {}".format(userid, colour))


def load_into(bot):
    bot.add_to_ctx(makeTeX)
