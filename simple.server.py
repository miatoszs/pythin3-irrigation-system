from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlparse
from urllib.parse import unquote
CONFIG_FILE = 'config.json'

class GetHandler(BaseHTTPRequestHandler):

    def getConf(self):
        config = {}
        global CONFIG_FILE
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        return(config)

    def parseQueryString(self, querysting):
        keyvalues = {}
        for keyvalue in querysting.split('&'):
            k,v = keyvalue.split('=')

            if not k in keyvalues:
                keyvalues[k] = unquote(v)
            elif type(keyvalues[k]) == "list":
                keyvalues[k].append(unquote(v))
            else:
                tmp = keyvalues[k]
                keyvalues[k] = []
                keyvalues[k].append(tmp)
                keyvalues[k].append(unquote(v))
        return keyvalues

    def read_text_file(self, path):
        if path.startswith('/'):
            path = path[1:]
        with open(path, "r", encoding='utf-8') as f:
            file_content = f.read()
        return(file_content)

    def generate_index_html(self):
        htmlcontent = ''
        zonelist = self.getConf()["zonelist"]

        for zone in zonelist:
            htmlcontent += '<h1>'+ zone["name"] +':'+ '</h1>'

            htmlcontent += '<form target="target">\n'
            htmlcontent += '<label for="appt-time">Start time</label>\n'
            programs = zone["program"]
            for program in programs:
                starttime = program['start']
                htmlcontent += '<div id="parentElement">'
                htmlcontent += '<div id="formblockElement">'
                htmlcontent += '<input id="appt-time" type="time" name="appt-time" value= '+ starttime +'>'+'\n'
                htmlcontent += '<br><label for="slider">interval: </label><span id="value"></span>'
                htmlcontent += f'<input name="interval" value="{program["interval"]}" type="range" min="" max="120" id="slider" class="slider"></label><br>'
                htmlcontent += '</div>'

                htmlcontent += '<input type = "button" class="button" name = "submit" value = "+" onclick=add(this) /><input type = "button" class="button" name = "submit" value = "-" onclick=remove(this) />'
                htmlcontent += '</div>'
            htmlcontent += '<input type = "submit" class="button" name = "submit" value = "Submit" />\n'
            htmlcontent += '</form>\n\n'
            ret = f'<html> <link rel="stylesheet" href="./style.css"><meta charset="utf-8"><body>\n{htmlcontent}</body><script  src="./rangevalue.js"></script><script  src="./addelement.js"></script></html>'
        return(ret)


    def do_GET(self):
        parsed_path = urlparse(self.path)
        if (parsed_path.path == '/' or parsed_path.path == '/index.html'):
            message = self.generate_index_html()
            self.send_response(200)
            self.send_header('Content-type','text/html')
        elif (parsed_path.path.endswith('.css') or parsed_path.path.endswith('.js') or parsed_path.path.endswith('.html')):
            self.send_response(200)
            if parsed_path.path.endswith('.js'):
                self.send_header('Content-type','application/javascript')
            elif parsed_path.path.endswith('.css'):
                self.send_header('Content-type','text/css')
            else:
                self.send_header('Content-type','text/html')
            message = self.read_text_file(parsed_path.path)
        else:
            self.send_response(200)
            message = '\n'.join([
                'CLIENT VALUES:',
                'client_address=%s (%s)' % (self.client_address,
                    self.address_string()),
                'command=%s' % self.command,
                'path=%s' % unquote(self.path),
                'real path=%s' % parsed_path.path,
                'query=%s' % unquote(parsed_path.query),
                'request_version=%s' % self.request_version,
                '',
                'SERVER VALUES:',
                'server_version=%s' % self.server_version,
                'sys_version=%s' % self.sys_version,
                'protocol_version=%s' % self.protocol_version,
                '',
                ])

        self.end_headers()
        self.wfile.write(bytes(message, "utf8"))
        if parsed_path.query:
            self.wfile.write(bytes(json.dumps(self.parseQueryString(parsed_path.query)), "utf8"))

        return

    def do_POST(self):
        content_len = int(self.headers.getheader('content-length'))
        post_body = self.rfile.read(content_len)
        self.send_response(200)
        self.end_headers()

        data = json.loads(post_body)

        self.wfile.write(data['foo'])
        return

if __name__ == '__main__':
    server = HTTPServer(('', 8080), GetHandler)
    print ('Starting server at http://localhost:8080')
    server.serve_forever()
