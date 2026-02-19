from app import create_app

app = create_app()

@app.route("/")
def home():
    return "API Flask - Kallpa Backend"

if __name__ == "__main__":
   app.run(port=5000)


