## Machine Learning Based Taiwan Stock Prediction (rewriting now)
---
#### Usage
* Start Services
  ```sh
  # at current directory
  $ docker-compose up

  # open another shell
  $ cd airflow/
  $ docker-compose -f docker-compose-LocalExecutor.yml up
  ```
* Stop Services
  ```sh
  # at current directory
  $ docker-compose down

  # another shell
  $ cd airflow/
  $ docker-compose -f docker-compose-LocalExecutor.yml down
  ```

#### Launch
Activate the environment, open two terminals and run following commands respectively
* start flask webserver ( `localhost:5000` )  
  user can view / add / remove stock history through webpage.

* visit Airflow webserver ( `localhost:8080` )


#### References
- docker-airflow
  - https://github.com/puckel/docker-airflow
- price dashboard
  - https://github.com/STATWORX/blog/tree/master/DashApp
  - https://www.statworx.com/at/blog/how-to-build-a-dashboard-in-python-plotly-dash-step-by-step-tutorial/
