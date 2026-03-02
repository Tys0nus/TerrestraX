import math

### Putpose : Time Shaping t --> s 

# class TimeLaw:
#     def __init__(self, T):
#         self.T = T

#     def s(self, t):
#         return t / self.T

def time_law(t: float, T: float) -> float:

    if t<0:
        return 0.0
    elif t>T:
        return 1.0
    
    tau = t / T
    s = 3*tau**2 - 2*tau**3
    sd = 6*tau*(1-tau) / T
    sdd = 6*(1-2*tau) / T**2
    return s, sd, sdd

def time_law_static(t: float, T: float) -> float:
    if T <= 0:
        raise ValueError("T must be > 0")
    tau = max(t, 0.0) / T
    return float(tau - math.floor(tau))
