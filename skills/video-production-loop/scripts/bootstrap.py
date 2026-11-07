"""Copy the self-contained starter into a NEW project directory."""
import argparse
from pathlib import Path
import shutil

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('destination',type=Path)
a=p.parse_args()
source=Path(__file__).resolve().parents[1]/'assets/remotion-starter'
target=a.destination.resolve()
if target.exists():
    raise SystemExit(f'Refusing to overwrite existing path: {target}')
if source==target or source in target.parents:
    raise SystemExit('Destination must be outside the bundled template')
shutil.copytree(source,target)
print(f'Created {target}\nNext: cd into the project, npm ci, npm run validate, npm run render')
