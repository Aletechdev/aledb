from .defaults import *

DEBUG = False

# if we are using os-environ, make sure that we have it set here
# otherwise, we want a KeyError to be thrown, rather than running
# production with what could be an unintentinally-set key
SECRET_KEY = os.environ['SECRET_KEY']
#SECRET_KEY = 'iv3^9^ccmwlfyeyp5q=%#z14p=p^6f1ujyzk8a3p*buzrg^2or'
