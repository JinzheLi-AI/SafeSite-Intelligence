"""Execute existing integration scenarios in isolated pytest temporary databases."""
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from evaluation.schema import MOCKED
from evaluation.metrics import workflow

def score(cases, outcomes):
    rows=[]
    for c in cases:
        outcome=outcomes.get(c['node'],{'passed':False,'error':'Missing scenario result'})
        rows.append({**c,**outcome})
    return {'status':MOCKED,'basis':'Real application services and SQLite; injected providers/synthetic images. No model accuracy.',
            'metrics':workflow(rows),'rows':rows}

def run(cases, backend, output):
    with tempfile.TemporaryDirectory(prefix='safesite-workflow-eval-') as temp:
        xml=Path(temp)/'scenarios.xml'
        completed=subprocess.run([sys.executable,'-m','pytest','-q',*[c['node'] for c in cases],
            '--junitxml='+str(xml)],cwd=backend,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (output/'workflow-pytest.txt').write_text(completed.stdout+'\n'+completed.stderr,encoding='utf-8')
        outcomes={}
        if xml.exists():
            (output/'workflow-junit.xml').write_bytes(xml.read_bytes())
            for node in ET.parse(xml).iter('testcase'):
                module=node.attrib.get('classname','').split('.')[-1]
                key='tests/'+module+'.py::'+node.attrib['name']
                failure=next((x for x in node if x.tag in ['failure','error','skipped']),None)
                outcomes[key]={'passed':failure is None,'error':None if failure is None else failure.attrib.get('message',failure.tag)}
        result=score(cases,outcomes)
        result['pytest_exit_code']=completed.returncode
        return result
