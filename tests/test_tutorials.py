import nbformat
import os
from nbconvert.preprocessors import ExecutePreprocessor

os.chdir('../tutorials')
notebooks = ['Getting started', 'Modeling and optimization', 'HTTP API']
for notebook in notebooks:
    print('Testing %s notebook.'%notebook)
    notebook_filename = '%s.ipynb'%notebook

    with open(notebook_filename) as f:
        nb = nbformat.read(f, as_version=4)
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    ep.preprocess(nb, {})
    with open('%s_executed.ipynb'%notebook, 'wt') as f:
        nbformat.write(nb, f)
    assert '%s_executed.ipynb'%notebook in os.listdir()
    print('Notebook passed!')
    os.remove('%s_executed.ipynb'%notebook)