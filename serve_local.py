import argparse
import http.server
import os
import socketserver


def main():
    parser = argparse.ArgumentParser(description="Serve generated static output locally.")
    parser.add_argument("--dir", dest="directory", default="output", help="Directory to serve (default: output)")
    parser.add_argument("--port", dest="port", type=int, default=8000, help="Port to serve on (default: 8000)")
    args = parser.parse_args()

    serve_dir = os.path.abspath(args.directory)
    if not os.path.isdir(serve_dir):
        raise SystemExit(f"Directory not found: {serve_dir}")
    handler = http.server.SimpleHTTPRequestHandler

    os.chdir(serve_dir)
    with socketserver.TCPServer(("", args.port), handler) as httpd:
        url = f"http://localhost:{args.port}/index.html"
        print(f"Serving {serve_dir} at {url}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
