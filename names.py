import random
import os
f = open(os.path.abspath(os.path.join("res","randnames")))
names = [x.strip().title() for x in f.readlines() if x.strip()]
f.close()

def name():
    return random.choice(names)