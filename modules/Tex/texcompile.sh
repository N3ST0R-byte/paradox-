cd tex/staging/$1/

chmod --quiet -R o+rwx .

rm -f $1.png $1.pdf

sudo -u latex timeout 1m pdflatex -no-shell-escape $1.tex > texout.log 2>&1

RET=$?
if [ $RET -eq 0 ];
then
 echo "";
elif [ $RET -eq 124 ];
then
 echo "Compilation timed out!";
else
    grep -A 10 -m 1 "^!" $1.log;
fi

if [ ! -f $1.pdf ];
then
  cp ../../failed.png $1.png
  exit
fi

convert -density 700 -quality 8 -trim +repage $1.pdf $1.png;
