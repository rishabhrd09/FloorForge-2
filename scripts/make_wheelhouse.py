"""Prepare Python wheels on a networked machine with the same OS/architecture/Python."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,"-m","pip","download","--only-binary=:all:","-r",str(root/"requirements.lock.txt"),"--dest",str(root/"wheelhouse")],check=True)
print("Copy the project and wheelhouse to the matching offline machine. Set FLOORFORGE_WHEELHOUSE to that folder before setup.")
