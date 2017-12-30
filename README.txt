To use this project clone the repo (requires git to be set up locally and
make a virtual environment:

>git clone https://github.com/clambygrum/nexradpy
>virtualenv <your virtualenv>
>pip install -r requirements.txt

Next install pyart:

>touch <yourvirtualenv>/lib/python2.7/site-packages/matplotlib/matplotlibrc
>echo "backend:TkAgg" > <yourvirtualenv>/lib/python2.7/site-packages/matplotlib/matplotlibrc
>git clone https://github.com/ARM-DOE/pyart
>python pyart/setup.py build_ext -i
>touch <your virtualenv>/lib/python2.7/site-packages/pyart.pth
>echo "/Users/<your username>/.../nexradpy/pyart" > <yourvirtualenv>/lib/python2.7/site-packages/pyart.pth

Now your working environment will be all set.

