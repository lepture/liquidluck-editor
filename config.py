import os.path
debug = True
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
