# filepath: /Ubuntu-24.04/home/jluna/projects/github/python-weather-app/wsgi.py
from main import app

server = app.server

if __name__ == "__main__":
    ## app run with binded port 8080, host and debug mode
    app.run_server(port=8080, host='0.0.0.0', debug=True)
    #app.run_server(debug=True, )

    ## to execute use the following command
    ## gunicorn --bind 0.0.0.0:8080 app:server