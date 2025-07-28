import os
from edsl import FileStore 
from conjure import Conjure

if not os.path.exists("GSS2024.dta"):
    fs = FileStore.pull('a92a71c3-0142-432f-b2a3-aa6fd9647263')
    fs.write("GSS2024.dta")

gss = Conjure("GSS2024.dta")
results = gss.to_results(verbose = True, sample_size = 1000)










