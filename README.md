## Machine Learning Based Taiwan Stock Prediction
---
#### Usage
```
usage: run.py [-h] [--init] [--start] [--update] [--train]

optional arguments:
  -h, --help  show this help message and exit
  --init      initialize database
  --start     start web serivce
  --update    get latest stocks' prices
  --train     train new model based on current dataset
```
#### Create Virtual Environment
Create venv and install packages
```
$ python3 -m venv env
$ source env/bin/activate

(env) $ pip install pip --upgrade
(env) $ pip install -r requirements.txt
```

#### **First Launch**
Use the following command to initialize sqlite database and Airflow database
```
(env) $ python run.py --init
```

#### Launch
Activate the environment, open two terminals and run following commands respectively
* start flask webserver ( `localhost:5000` )  
user can view/add/remove stock history through webpage.
```
(env) $ python run.py --start
```
* start Airflow scheduler & webserver ( `localhost:8080` )
```
(env) $ python run.py --update
```

#### Update ML model
Use data in database and train a new model (LSTM)   
* Once new stock is added, the ML model needs to be retrained
```
(env) $ python run.py --train
```