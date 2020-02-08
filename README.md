## Machine Learning Based Taiwan Stock Predictor
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
#### **First Launch**
Use the following command to initialize sqlite database and Airflow database
```
$ python run.py --init
```

#### Launch
Activate the environment, open two terminals and run following commands respectively
* start flask webserver ( localhost:5000 )  
user can view/add/remove stock history through webpage.
```
$ python run.py --start
```
* start Airflow scheduler & webserver ( localhost:8080 )
```
$ python run.py --update
```

#### Update ML model
Use data in database and train a new model (RNN)
```
$ python run.py --train
```