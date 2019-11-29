**What is LaTeX (in discord)?**
LaTeX is a fun and easy markup language which lets you produce nicely formatted text and equations using simple commands.

**How do I use it?**
If LaTeX recognition is enabled, I will automatically scan every message you send for LaTeX code.
Your code will compiled using your personal LaTeX configuration, and the result will be posted with the following reactions.
` delete`: Delete the output.
`showtex`: Show the original source and any compile errors.
` delsrc`: Delete the source message.

Try this now by typing `$\frac{{a}}{{b}}$` below! You can also see an example in the attached image.
```md
# Tips
• All formulas must be surrounded by dollars like $this$, or other maths delimiters.
• To display multiple lines, use two linebreaks or \\ to end a line.
• If codeblocks appear, only the contents of the blocks will be rendered.
```
If inline LaTeX is disabled, you can still render LaTeX using `{prefix}tex <code>` or one of its aliases.

**Customisation and configuration**
In addition to the following options, the LaTeX output is highly configurable through the **preamble** system.
Run `{prefix}help preamble` to learn more!
```lua
tex -colour -- Change your rendering colourscheme, or list valid colourschemes.
tex -keepmsg -- Keep or delete your source message after compilation.
tex -alwaysmath -- Whether the tex command should render in maths mode or text mode.
tex -name -- Whether your name is shown above the output image.
tex -allowother -- Whether other users can use the showsrc reaction on your output.
```

**But wait, there's more!**
LaTeX can be used for many amazing things! Check out some of our examples in the menu below!

The TeXit team have written a brief cheatsheet to help you get started, available at <http://files.paradoxical.pw/latex_cheatsheet.pdf>.
If you have any questions about LaTeX or want to hang out with other LaTeX users, join the LaTeX support server here: https://discord.gg/6zmgC2S
