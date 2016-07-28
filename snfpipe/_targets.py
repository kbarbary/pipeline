
"""Parsing the HTML page for IAUC supernovae."""

import re
import string

from ._utils import RADec

__all__ = ["IAUCTarget", "SNFTarget", "read_iauc_targets", "read_snf_targets"]


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
        return ("IAUCTarget({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})"
                .format(self.Galaxy, self.Mag, self.Name, self.Ra,
                        self.Dec, self.Type, self.Iauc))


class SNFTarget(object):
    def __init__(self, Name, OName, Ra, Dec, VMag, Type, Kind, File, x, y):
        self.Name = Name
        self.OName = OName
        self.Ra = Ra
        self.Dec = Dec
        self.VMag = VMag
        self.Type = "Unknown"
        self.Kind = None
        self.File = None
        self.x = -1
        self.y = -1

    def __repr__(self):
        return ("SNFTarget({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, "
                "{!r}, {!r})"
                .format(self.Name, self.OName, self.Ra, self.Dec, self.VMag,
                        self.Type, self.Kind, self.File, self.x, self.y))


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


def read_iauc_targets(fname):
    """Parse IAUCTargets from HTML page"""

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


def read_snf_target_line(words, kind):
    words = [word.strip() for word in words]

    if kind in ("StdStar", "DbleStar"):
        oname, ra_str, dec_str, file_, x_str, y_str, vmag, type_ = words[0:8]
        name = oname

    elif kind == "Candidate":
        name, oname, _, ra_str, dec_str, file_, x_str, y_str = words[0:8]
        if not name:
            name = oname
        if not oname:
            oname = None
        vmag = "100.0"
        type_ = "Unknown"

    else:
        raise ValueError("unknown kind: {}".format(kind))

    # parse RA, Dec to decimal
    ra = RADec(ra_str, "RA").Deg()
    dec = RADec(dec_str, "Dec").Deg()

    # parse x, y location
    try:
        x = float(x_str)
        y = float(y_str)
    except ValueError:
        x = -1
        y = -1

    return SNFTarget(name, oname, ra, dec, float(vmag), type_, kind, file_,
                     x, y)


def read_snf_targets(fname):
    """Read the FindingChart format file """

    f = open(fname)
    targets = []

    # loop on the file
    kind = ""
    for line in f.readlines():
        line = line.strip()
        if line.startswith("#"):
            kind = line.split()[1].strip()
        else:
            words = line.split('|')
            if len(words) > 4 and words[1].strip() != "^":
                    targets.append(read_snf_target_line(words[1:], kind))

    f.close()

    return targets
