import os
import shutil

from tex_config import default_preamble

"""
Provides a single context utility to compile LaTeX code from a user and return any error message
"""

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

# Dictionary of valid colours and the associated transformation commands
colourschemes = {}
colourschemes["transparent_white"] = r"convert {image} -negate -fuzz 5% -transparent 'rgb(20, 20, 20)' {image}"
colourschemes["transparent_black"] = r"convert {image} -fuzz 5% -transparent 'rgb(223, 223, 223)' {image}"

colourschemes["white"] = r"convert {image} -fuzz 5% -fill white -opaque 'rgb(223, 223, 223)' {image}"
colourschemes["black"] = r"convert {image} -negate -fuzz 5% -fill black -opaque 'rgb(20, 20, 20)' {image}"
colourschemes["darkgrey"] = r"convert {image} -negate -fuzz 5% -fill 'rgb(35, 39, 42)' -opaque 'rgb(20, 20, 20)' {image}"

colourschemes["grey"] = r"convert {image} -negate -fuzz 5% -fill 'rgb(54, 57, 63)' -opaque 'rgb(20, 20, 20)' {image}"
colourschemes["gray"] = colourschemes["grey"]
colourschemes["default"] = colourschemes["grey"]

colourschemes["light"] = None
colourschemes["dark"] = r"convert {image} -negate {image}"

# Script which pads images to a minimum width of 1000
pad_script = r"""
height=`convert {image} -format "%h" info:`
width=`convert {image} -format "%[fx:w]" info:`
minwidth=1000
newwidth=$(( width > minwidth ? width : minwidth ))

convert {image} -background transparent -extent ${{newwidth}}x${{height}} {image}
"""

# Path to the compile script
compile_path = os.path.join(__location__, "texcompile.sh")

# Header for every LaTeX source file
header = "\\documentclass[preview, border=10pt, 12pt]{standalone}\
          \n\\nonstopmode"

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
