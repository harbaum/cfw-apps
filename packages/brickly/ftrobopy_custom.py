#
# ftroboypy_custom wrapper
#
# Hide incompatible API/firmware changes from the app
#

# TODO:
# - suppress audio calls in direct mode

import ftrobopy
import os

class ftrobopy_custom(ftrobopy.ftrobopy):
    # overwrite constructor
    def __init__(self, host="127.0.0.1", port=65000):
        # check for 
        txt_ip = os.environ.get('TXT_IP')
        if txt_ip:
            ftrobopy.ftrobopy.__init__(self,txt_ip, port)
        else:
            # no ip given, try to connect locally
            # on newer versions using the direct mode first
            if float(ftrobopy.__version__) > 1.56:
                ftrobopy.ftrobopy.__init__(self,"auto")
            else:
                ftrobopy.ftrobopy.__init__(self,"localhost", port)
