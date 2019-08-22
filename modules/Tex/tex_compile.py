import os
import shutil

from tex_config import default_preamble

"""
Provides a single context utility to compile LaTeX code from a user and return any error message
"""

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def gencolour(colour, negate=True):
    """
    Build the colour conversion command for the provided colour, negating black text if required
    """
    return r"convert {{image}} {} -bordercolor transparent -border 40 \
        -background {} -flatten {{image}}".format("+negate" if negate else "", colour)


# Dictionary of valid colours and the associated transformation commands
colourschemes = {}

colourschemes["white"] = gencolour("white", False)
colourschemes["black"] = gencolour("black")

colourschemes["light"] = gencolour("'rgb(223, 223, 233)'", False)
colourschemes["dark"] = gencolour("'rgb(20, 20, 20)'")

colourschemes["gray"] = colourschemes["grey"] = gencolour("'rgb(54, 57, 63)'")
colourschemes["darkgrey"] = gencolour("'rgb(35, 39, 42)'")

colourschemes["trans_white"] = r"convert {image} +negate -bordercolor transparent -border 40 {image}"
colourschemes["trans_black"] = None
colourschemes["transparent"] = colourschemes["trans_white"]

colourschemes["default"] = colourschemes["grey"]


# Script which pads images to a minimum width of 1000
pad_script = r"""
width=`convert {image} -format "%[fx:w]" info:`
minwidth=1000
extra=$((minwidth-width))

if (( extra > 0 )); then
    convert {image} -gravity East +antialias -splice ${{extra}}x {image}
fi
"""

# Path to the compile script
compile_path = os.path.join(__location__, "texcompile.sh")

# Header for every LaTeX source file
header = "\\documentclass[preview, border=10pt, 13pt]{standalone}\
    \\usepackage[warnunknown, fasterrors, mathletters]{ucs}\
    \\usepackage[utf8x]{inputenc}\
    \\IfFileExists{eggs.sty}{\\usepackage{eggs}}{}\
    \n\\nonstopmode"

"""
# Alternative header to support discord emoji, but not other unicode
header = "\\documentclass[preview, border=10pt, 12pt]{standalone}\
    \\IfFileExists{eggs.sty}{\\usepackage{eggs}}{}\
    \n\\nonstopmode"
"""

# The format of the source to compile
to_compile = "{header}\
    \n{preamble}\
    \n\\begin{{document}}\
    \n{source}\
    \n\\end{{document}}"


async def makeTeX(ctx, source, userid, preamble=default_preamble, colour="default", header=header, pad=True):
    path = "tex/staging/{}".format(userid)
    os.makedirs(path, exist_ok=True)

    fn = "{}/{}.tex".format(path, userid)

    with open(fn, 'w') as work:
        work.write(to_compile.format(header=header, preamble=preamble, source=source))
        work.close()

    # Build compile script
    script = "{compile_script} {id}\
        \ncd {path}\
        \n{colour}\
        \n{pad}".format(compile_script=compile_path,
                        id=userid, path=path,
                        colour=colourschemes[colour] or "",
                        pad=pad_script if pad else "").format(image="{}.png".format(userid))

    # Run the script in an async executor
    return await ctx.run_sh(script)


def setup_structure():
    """
    Set up the initial tex directory structure,
    including copying the required resources.
    """
    os.makedirs("tex/staging", exist_ok=True)
    shutil.copy(os.path.join(__location__, "failed.png"), "tex")


def load_into(bot):
    setup_structure()
    bot.add_to_ctx(makeTeX)
