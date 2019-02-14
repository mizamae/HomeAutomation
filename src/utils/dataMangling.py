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
    if (int(number) & mask)!=0:
        return True
    else:
        return False

def localizeTimestamp(timestamp):
    from tzlocal import get_localzone
    local_tz=get_localzone()

    timestamp = local_tz.localize(timestamp.replace(tzinfo=None))

    timestamp=timestamp+timestamp.utcoffset()
    return timestamp
            
def dec2bin(x):
    data=[]
    for i in range(0,8):
        try:
            x=int(x)
            data.append(1 if (x & (1<<int(i)))>0 else 0)
        except:
            data.append(None)
    return data   

def remove_outlier(df_in, col_name):
    import pandas as pd
    import numpy as np
    #df_in.fillna(inplace=True,method='ffill')
    #df_in.fillna(inplace=True,method='bfill')
    q1 = df_in[col_name].quantile(0.25)
    q3 = df_in[col_name].quantile(0.75)
    iqr = q3-q1 #Interquartile range
    fence_low  = q1-1.5*iqr
    fence_high = q3+1.5*iqr
    df_out = df_in.loc[(df_in[col_name] > fence_low) & (df_in[col_name] < fence_high)]
    
    return df_out     