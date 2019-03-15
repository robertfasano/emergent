call conda.bat create -n emergent python=3.7 --yes
call activate emergent
cd /emergent
python setup.py develop
cd /emergent/emergent
