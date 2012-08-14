import os.path
debug = True
host = '0.0.0.0'
port = 8000
pid = '/tmp/liquidluck-editor.pid'
site_name = 'Felix'
cookie_secret = '123'

project_folder = os.path.expanduser('~/workspace/site/lepture.com')
content_folder = os.path.join(project_folder, 'content')

authors = [
    'someone@gmail.com'
]

builder = {
    'cwd': project_folder,
    'cmd': 'liquidluck build',
}
