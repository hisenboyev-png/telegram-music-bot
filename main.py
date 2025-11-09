from bot import main
from waitress import serve

if __name__ == "__main__":
    serve(main, host="0.0.0.0", port=8080)