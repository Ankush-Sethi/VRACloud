import winrm
def handler(context, inputs):
    session=winrm.Session('xxx',auth=('administrator','xxxx'),transport='basic')
    tmpScript = 'hostname'
    run=session.run_ps(tmpScript)
    print(run)
