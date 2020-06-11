import numpy as np
from main import main

def test_main():
    P,V,S = main(1,plotting=False)
    assert np.isclose(S[10], 0.7270660798329192, atol=1e-14)

def test_main2():
    P,V,S = main(1,plotting=False)
    assert np.isclose(P[5,0,0], -1.2973481310166959, atol=1e-14)
