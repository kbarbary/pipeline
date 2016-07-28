from math import pi, sin, cos, acos
    
class RADec(object):
    "Class build a RA DEC object from any kind of RA DEC"

    def __init__(self, coorx, xtype):
        # Accepted format :    HH:MM:SS.s
        # in input             HH MM SS.s
        #                      deg.xxxxxx

        ltype = xtype.upper()

        if (ltype != "RA" and ltype != "DEC"):
            raise ValueError('Given Type is not RA or DEC')
        self.Type = ltype

        # Work coord
        found = 0
        if (type(coorx) is str):
            coor1 = coorx.strip()
            coor2 = coor1.split("-")
            if len(coor2) == 1:
                coor = coor2[0]
                sign = 1
            elif len(coor2) == 2:
                coor = coor2[1]
                sign = -1
            else:
                raise ValueError("Format for Given RA or DEC incorect : %s" %
                                 coorx)
            ra_str=coor.split(":")
            if len(ra_str) == 1:
                ra_str = coor.split(" ")
                if len(ra_str) == 1:
                    Deg = float(coor) * sign
                    found = 1
        else:
            Deg = coorx
            found = 1

        if found == 1:
            sign = 1
            if Deg < 0:
                sign = -1
            if xtype == "RA":
                hour = abs(Deg) / 15
            else:
                hour = abs(Deg)
            self.H = int(hour)
            self.M = int((hour - float(self.H)) * 60.)
            self.S = (int(((hour - float(self.H)) * 3600. -
                           float(self.M) * 60.) * 100. + 0.5)) / 100.
            if int(self.S) >= 60:
                self.S = self.S - 60.
                self.M = self.M + 1
            if self.M > 60:
                self.M = self.M - 60
                self.H = self.H + 1
            if (  xtype=="RA" and self.H >= 24 ) :
                self.H=self.H-24
            elif (  xtype!="RA" and self.H >= 90 ) :
                self.H=self.H-90
            self.H=self.H
            self.sign=sign

        else:
            self.sign=sign
            if ( len(ra_str) == 2 ) :    
                self.H=int(ra_str[0])
                self.M=int(float(ra_str[1]))
                self.S=(float(ra_str[1])-self.M)*60.
            elif ( len(ra_str) == 3 ) :    
                self.H=int(ra_str[0])
                self.M=int(ra_str[1])
                self.S=float(ra_str[2])
            elif ( len(ra_str) == 4 ) :
                self.H=int(ra_str[0]+ra_str[1])
                self.M=int(ra_str[2])
                self.S=float(ra_str[3])
            else :
                raise ValueError("RA or DEC incorrect : " + com)
        
    def __repr__(self):
        return str(self)

    def __str__(self):
        if self.sign > 0 :
            return "%02d:%02d:%05.2f" % ( self.H , self.M , self.S )
        else :
            return "-%02d:%02d:%05.2f" % ( self.H , self.M , self.S )

    def __add__(self, other):
        if self.Type != other.Type :
            raise ValueError("Both objects of different type : %s # %s " %
                             (self.Type, other.Type))
        return RADec(self.Deg() + other.Deg(), self.Type)       

    def __sub__(self,other):
        if self.Type != other.Type :
            raise ValueError("Both objects of different type : %s # %s " %
                             (self.Type, other.Type))
        return RADec(self.Deg() - other.Deg(), self.Type)       

    def Deg(self):
        if ( self.Type=="RA" ):
            xDeg=(abs(float(self.H))+(float(self.M)+self.S/60.)/60.)*15.
        else:
            xDeg=abs(float(self.H))+(float(self.M)+self.S/60.)/60.
        if self.sign < 0:
            xDeg = -xDeg
        return xDeg

    def Rad(self):
        return self.Deg() * pi / 180.

    def SubOffset(self, offset):
        # it seems tah the offset just need to be / 3600 ! to be in s,  
        delta = offset/3600.
        # 
        new = RADec(self.Deg() - delta, self.Type)
        self.sign = new.sign
        self.H = new.H
        self.M = new.M
        self.S = new.S


def AngDist(r,d,r1,d1):
    "Angular distance between 2 directions ra,dec , ra1,dec1 given in radian"

    try:
        result = acos(cos(r)*cos(d)*cos(r1)*cos(d1)+sin(r)*cos(d)*sin(r1)*cos(d1)+sin(d)*sin(d1))
    except:
        # to close to the boundary ?
        result = cos(r)*cos(d)*cos(r1)*cos(d1)+sin(r)*cos(d)*sin(r1)*cos(d1)+sin(d)*sin(d1)

        if abs(abs(result)-1.) > 0.001 :
            raise ValueError("AngDist  error !!!! should have been ok if cos(ang)~1. or -1. but not : ", result)
        if result > 0.:
            return 0.
        else:
            return pi

    return result

def AngDistD(r0, d0, r01, d01):
    "Angular distance between 2 directions ra,dec , ra1,dec1 given in Degree"
    r = r0 * pi / 180.
    d = d0 * pi / 180.
    r1 = r01 * pi / 180.
    d1 = d01 * pi / 180.

    return AngDist(r, d, r1, d1) * 180. / pi
