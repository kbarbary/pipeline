#!/usr/bin/env python
"""Define a snf pipeline workflow in Python and create a makefile
that will execute it"""

import itertools
import json
import os
from os.path import join



class Makefile(object):
    def __init__(self, path):
        self._file = open(path, 'w')

        # keep track of product directories that need rules
        self._dirs = set()

    def add_comment(self, comment):
        self._file.write('# {}\n\n'.format(comment))

    def add_rule(self, command, produces, depends=None):
        """Add rule(s) to a makefile."""

        if type(produces) not in (list, tuple):
            produces = (produces,)

        # get depends as a string
        if depends is None:
            depends = ''
        elif type(depends) in (list, tuple):
            depends = ' '.join(depends)

        # get commands as a string
        if type(command) not in (list, tuple):
            command = (command,)
        cmd = '\t' + '\n\t'.join(command) + '\n'

        # get directory dependencies
        dirnames = set()
        for product in produces:
            dirname = os.path.dirname(product)
            if dirname != '':
                dirnames.add(dirname)
        
        # add directory names to globals
        self._dirs.update(dirnames)

        # add directories (if any) to depenencies
        depends += ' '.join(dirnames)

        self._file.write('{} : {}\n{}\n'
                         .format(' '.join(produces), depends, cmd))

    def close(self):
        # directory rules
        for dirname in self._dirs:
            self._file.write('{} :\n\tmkdir -p {}\n\n'
                             .format(dirname, dirname))

        # default rule
        #self._file.write('.DEFAULT_GOAL: {}\n\n')
                         
        self._file.close()

    def __del__(self):
        # call close if we didn't already
        if not self._file.closed:
            self.close()

                            

if __name__ == "__main__":

    ROOTDIR = "/project/projectdirs/snfactry/processing/0203-CABALLO"
    TAG = "0203-CABALLO"
    CUBEFIT_MODEL = ROOTDIR + "/cubefit-model"
    sne = ["PTF09fox", "PTF09foz"]

    os.chdir(ROOTDIR)

    # TODO: write to tempfile by default
    mf = Makefile('makefile')

    for sn, channel in itertools.product(sne, 'BR'):

        config = "cubefit-config/{}/{}_{}.json".format(sn, sn, channel)
        cubefit_subtract_outprefix = join("cubes-galsub", sn)

        # get input files, ouput files to cubefit and cubefit-subtract
        # from the config file
        with open(config) as f:
            conf = json.load(f)
            cubefit_inputs = [os.path.join("cubes-cal-corr", f)
                              for f in conf["filenames"]]
            cubefit_subtract_outputs = \
                [os.path.join(cubefit_subtract_outprefix, f)
                 for f in conf["outnames"] + conf["sn_outnames"]]

        # cubefit rule
        cubefit_output = ("cubefit-model/{}/{}_{}.fits"
                          .format(sn, sn, channel))
        logfile = "cubefit-model/{}/{}_{}.log".format(sn, sn, channel)
        cmd = ('cubefit {} {} --dataprefix=cubes-cal-corr --logfile={}'
               '--mu_wave=0.07 --mu_xy=0.001 '
               '--psftype=gaussian-moffat --loglevel=info'
               .format(config, cubefit_output, logfile))

        mf.add_rule(cmd, cubefit_output, cubefit_inputs + [config])

        # cubefit-subtract
        cmd = ('cubefit-subtract {} {} --dataprefix=cubes-cal-corr'
               '--outprefix={}'
               .format(config, cubefit_output, cubefit_subtract_outprefix))
        mf.add_rule(cmd, cubefit_subtract_outputs,
                    cubefit_inputs + [config, cubefit_output])

    mf.close()
