#!/usr/bin/env python
# coding: utf-8
# Copyright 2013 Landon Wu
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib


URL_RULE = "^http://(?P<HOST>[A-Za-z0-9\-\.]+)(?P<PORT>:[0-9]+)?(?P<PATH>.*)$"
URL_MATCH_RE = re.compile(URL_RULE, re.I)


def help():
    print "httpclient.py [GET/POST] [URL]\n"


class HTTPResponse(object):

    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

    def __str__(self):
        return "CODE: %s\n%s" % (self.code, self.body)


class HTTPRequest(object):

    def __init__(self, method, url, args=None):
        self.method = method
        self.url = url
        self.args = args

        self._header = None
        self.host = None
        self.port = None
        self.path = None
        self.data = ""

        self.parse_url()

    def get_host_tuple(self):
        return (self.host, self.port)

    def get_header(self):
        if self._header is None:
            self._build_header()

        return self._header

    def _build_data(self):
        if self.method == "POST" and self.args is not None:
            self.data = urllib.urlencode(self.args)

    def _build_header(self):
        header = "%s %s HTTP/1.1\r\n" % (self.method, self.path)
        header += "Host: %s:%d \r\n" % (self.host, self.port)
        header += "User-Agent: CMPUT404 Client \r\n"
        header += "Accept: text/plain\r\n"

        if self.method == 'POST':
            self._build_data()
            header += "Content-Type: application/x-www-form-urlencoded\r\n"
            header += "Content-Length: %d \r\n" % len(self.data)

        header += "Connection: close\r\n\r\n"

        self._header = header
        print header

    def parse_url(self):
        if not self.url.startswith("http:"):
            self.url = "http://" + self.url

        url_result = URL_MATCH_RE.search(self.url)

        if not url_result:
            # cannot find host name.
            pass

        g_dict = url_result.groupdict()
        self.host = g_dict['HOST']
        self.port = int(g_dict['PORT'][1:]) if g_dict['PORT'] else 80
        self.path = g_dict['PATH'] if g_dict['PATH'] else '/'

        # build the query
        self._build_query()

    def _build_query(self):
        if self.method == "GET" and self.args is not None:
            query = urllib.urlencode(self.args)

            if "?" in self.path:
                url_path, query_path = self.path.split('?')
                self.path = url_path
                query = query_path + "&" + query

            self.path = self.path + "?" + query


class HTTPClient(object):

    def connect(self):
        #print self._request_obj.get_host_tuple()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(self._request_obj.get_host_tuple())
        except socket.error as e:
            print "Socket Error: %s" % e
            sys.exit()

        return sock

    def get_code(self, data):
        return int(data.split('\r\n')[0].split()[1])

    def get_headers(self, data):
        return data.split('\r\n\r\n')[0]

    def get_body(self, data):
        return data.split('\r\n\r\n')[1]

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return str(buffer)

    def request(self, method, url, args):
        self._request_obj = HTTPRequest(method, url, args)

        conn = self.connect()
        conn.sendall(self._request_obj.get_header())

        # send post data
        if self._request_obj.data:
            conn.sendall(self._request_obj.data)

        # finish sending, waiting for response.
        data = self.recvall(conn)

        header = self.get_headers(data)
        code = self.get_code(header)
        body = self.get_body(data)

        return HTTPResponse(code, body)

    def GET(self, url, args=None):
        return self.request('GET', url, args)

    def POST(self, url, args=None):
        return self.request('POST', url, args)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST(url, args)
        else:
            return self.GET(url, args)


if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print client.command(sys.argv[2], sys.argv[1])
    else:
        print client.command(sys.argv[1])
