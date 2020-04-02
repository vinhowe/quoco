def minutes(timestr: str): 
    hours_ct = int(timestr[:timestr.index('h')]) 
    minutes_ct = int(timestr[timestr.index('h') + 1 : timestr.index('m')]) 
    return (hours_ct * 60) + minutes_ct              
