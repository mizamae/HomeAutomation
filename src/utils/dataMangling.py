def Bytes2Float32(binnumber):
        
    if (binnumber & 1<<31)>0:
        sign=-1
    else:
        sign=1
    exponent=((binnumber>>23)    &    0xFF)-127
    significand=(binnumber&~(-1<<23));
    if    (exponent    ==    128):
        if significand:
            return    None 
        else:
            return    None 
    elif    (exponent    ==    -127):
        if    (significand==0):    
            return    sign    *    0.0
    else:
        significand=(significand|(1<<23))/(1<<23);
    return sign*significand*2**exponent

def checkBit(number,position):
    mask=1<<position
    if (number & mask)!=0:
        return True
    else:
        return False
        