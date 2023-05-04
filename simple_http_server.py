import http.server
import os
import socketserver
import sys

from argparse import ArgumentParser

# コマンドライン引数を解析
parser = ArgumentParser(description='Simple HTTP Server')
parser.add_argument('-p', '--port', type=int, default=8000,
                    help='Specify the port number (default: 8000)')
args = parser.parse_args()

# ドキュメントルートディレクトリへ移動
os.chdir('docs/_build/html')

# ポート番号を指定
PORT = args.port

Handler = http.server.SimpleHTTPRequestHandler

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving on port {PORT}")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down the server.")
    httpd.shutdown()
    sys.exit(0)
