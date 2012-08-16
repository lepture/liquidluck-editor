import os
import re
import datetime
import subprocess
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.auth
import tornado.escape
import config
from liquidluck.readers.markdown import markdown
from liquidluck.tools.webhook import Daemon


DEMO = '''# title

- date: %s
- link: http://lepture.com
- category: trends|economy|life|culture
- author: lepture

----------------------

write your comment here
'''


def create_demo():
    now = datetime.datetime.now()
    return DEMO % now.strftime('%Y-%m-%d %H:%M')


def content_files():
    for root, dirs, files in os.walk(config.content_folder):
        for f in files:
            path = os.path.join(root, f)
            yield path.replace(config.content_folder, '', 1).lstrip('/')


def read_file(filename):
    path = os.path.join(config.content_folder, filename)
    if not os.path.exists(path):
        return None
    f = open(path, 'r')
    try:
        content = f.read()
    except:
        content = None
    finally:
        f.close()

    return content


def write_file(filename, content):
    path = os.path.join(config.content_folder, filename)
    content = tornado.escape.utf8(content)
    f = open(path, 'w')
    f.write(content)
    f.close()
    return content


def rename_file(old, new):
    old = os.path.join(config.content_folder, old)
    if not os.path.exists(old):
        return
    new = os.path.join(config.content_folder, new)
    os.rename(old, new)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie('user')
        if not user_json:
            return None
        user = tornado.escape.json_decode(user_json)
        if user['email'] not in config.authors:
            return None
        return user

    def render_string(self, template_name, **kwargs):
        kwargs['config'] = config
        return super(BaseHandler, self).render_string(template_name, **kwargs)


class AdminHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('admin.html', files=content_files())


class PostHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, filename):
        content = None
        if filename == 'new':
            # new post
            now = datetime.datetime.now()
            filename = '%s/new-filename.md' % now.year
        else:
            content = read_file(filename)

        if content is None:
            content = create_demo()

        self.render('post.html', filename=filename, content=content)

    @tornado.web.authenticated
    def post(self, filename):
        newfile = self.get_argument('filename', None)
        content = self.get_argument('content', None)
        if not newfile or not content:
            self.write({'stat': 'fail', 'msg': 'need filename and content'})
            return

        if newfile != filename and filename != 'new':
            rename_file(filename, newfile)

        write_file(newfile, content)
        self.write({'stat': 'ok'})

    @tornado.web.authenticated
    def delete(self, filename):
        pass


class LoginHandler(BaseHandler, tornado.auth.GoogleMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("openid.mode", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect(ax_attrs=["name", "email"])

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Google auth failed")
        self.set_secure_cookie("user", tornado.escape.json_encode(user))
        self.redirect("/-admin/")


class BuildHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        cmd = config.builder['cmd']
        cwd = config.builder['cwd']
        subprocess.call(cmd.split(), cwd=cwd)
        self.write({'stat': 'ok'})


class PreviewHandler(BaseHandler):
    def post(self):
        content = self.get_argument('content', '')
        content = re.sub(r'\r\n|\r|\n\r', '\n', content)
        header = ''
        body = ''
        recording = True

        for line in content.split('\n'):
            if recording and line.startswith('---'):
                recording = False
            elif recording:
                header += line + '\n'
            else:
                body += line + '\n'

        self.write({'html': markdown(body)})


def main():
    tornado.options.parse_command_line()
    settings = {
        'debug': config.debug,
        'cookie_secret': config.cookie_secret,
        'login_url': '/-admin/login',
        'static_path': os.path.join(config.root, '_static'),
        'static_url_prefix': '/-admin/static/',
        'template_path': os.path.join(config.root, '_templates'),
    }
    application = tornado.web.Application([
        (r'/-admin/', AdminHandler),
        (r'/-admin/login', LoginHandler),
        (r'/-admin/build', BuildHandler),
        (r'/-admin/preview', PreviewHandler),
        (r'/-admin/post/(.*)', PostHandler),
    ], **settings)

    server = tornado.httpserver.HTTPServer(application, xheaders=True)
    server.listen(config.port, config.host)
    tornado.ioloop.IOLoop.instance().start()


class ServerDaemon(Daemon):
    def run(self):
        main()


def deamon_server(command='start'):
    if config.debug:
        main()
        return
    d = ServerDaemon(config.pid)
    if command == 'start':
        d.start()
    elif command == 'stop':
        d.stop()
    elif command == 'restart':
        d.restart()
    else:
        main()


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        deamon_server(sys.argv[1])
    else:
        print('python app.py start|stop|restart')
