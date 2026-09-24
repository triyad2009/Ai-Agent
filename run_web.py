from web_server import app
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, threaded=True, debug=False)
