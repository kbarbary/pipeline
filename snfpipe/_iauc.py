
"""Parsing the HTML page for IAUC supernovae."""

import re
import string

from ._utils import RADec

__all__ = ["read_iauc_targets"]


def read_iauc_targets(fname):
    """Generate the file with IUAC target using the web"""

    html_doc = open(fname).read()

    html_doc = html_doc[html_doc.find('<pre>')+6 : html_doc.find('</pre>')]

    # remove HTML tags and get only SNe from >= 2000
    lines = [i for i in re.sub('<.+?>', '', html_doc).split('\n')
             if i and i[0] in string.digits and int(i[:4]) >= 2000]

    targets = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            targets.append(read_iauc_line(line))

    validate_iauc_targets(targets)

    return targets


class IAUCTarget(object):
    def __init__(self, Galaxy, Mag, Name, Ra, Dec, Type, Iauc):
        self.Galaxy = Galaxy
        self.Mag = Mag
        self.Name = Name
        self.Ra = Ra
        self.Dec = Dec
        self.Type = Type
        self.Iauc = Iauc

    def __repr__(self):
        return "IAUCTarget({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(self.Galaxy, self.Mag, self.Name, self.Ra, self.Dec, self.Type, self.Iauc)


def read_iauc_line(l):

    #RP - welcome to regex hell
    m = re.search('(?P<sn>\d{4}[A-Z]?[a-z]{0,2})\s{2,3}'
                  # this may happen to be only whitespace
                  '(?P<galinfo>.+)'
                  # CBET / IAUC
                  '(?P<galref>[A-Z]{4}\s+\d{1,})\s+'
                  '(?P<ra>\d+\s+\d+\s+\d+(\.\d+)?)\s+'
                  '(?P<dec>[\+\-\_]?\s?\d+\s+(\d+\s+)?\d+(\.\d+)?)\s+'
                  '(?P<ref>([A-Z]{4}\s+\d{1,})\s+|\s+)'
                  '(?P<type>.+(?=\d{4}[A-Z]?[a-z]{0,2}))', l).group
    
    # test is the galaxy info is filled (ie. we can find a date)
    if re.search('(.+(?=\d{4}\s+\d{2}))', m('galinfo')) is not None:

        m2 = re.search('(?P<galaxy>.+)'
                       '(?P<date>\d{4}\s+\d{2}\s+\d{2})\s+'
                       '(?P<galra>\d{1,}\s+\d{1,}\.\d)\s+'
                       '(?P<galdec>\+?\-?\s?\d+\s+\d+)\s+'
                       '(?P<offmag>.+)', m('galinfo')).group

        galaxy = m2('galaxy').strip()
        try:
            mag = float(m2('offmag').strip().split()[-1])
        except (ValueError, IndexError):
            mag = 99.

    else:
        galaxy = m('galinfo').strip()[:16].strip()
        mag = 99.

    name = m('sn').strip()

    #make proper RA DEC for RaDec usage
    ra_str = ' '.join(m('ra').strip().split())
    dec_str = ' '.join(m('dec').strip().split()).replace('_','-')
    ra = RADec(ra_str, "RA").Deg()
    dec = RADec(dec_str, "DEC").Deg()

    type = m('type').strip()
    try:
        iauc = int(m('ref').strip().split()[-1])
    except (ValueError, IndexError):
        iauc = 0

    return IAUCTarget(galaxy, mag, name, ra, dec, type, iauc)


def validate_iauc_targets(targets):
    """Check that there are no weird entries in the IAUC list

    One should add tests here for improperly formatted IAUC entries.

    Parameters
    ----------
    targets: list of IAUCTarget instances
    """

    # are there SNe with exactly the same RA,Dec? (True if all locations are unique)
    same_radec = (len([(tgt.Ra, tgt.Dec) for tgt in targets]) ==
                  len(set([(tgt.Ra, tgt.Dec) for tgt in targets])))
    if not same_radec:
        raise RuntimeError("two or more SNe with exactly the same RA, Dec")

    # are there SNe with a galaxy name starting with a digit?
    galaxy_name = len([tgt for tgt in targets
                       if tgt.Galaxy and tgt.Galaxy[0] in string.digits]) == 0
    if not galaxy_name:
        raise RuntimeError('there are galaxy names starting with a digit')
