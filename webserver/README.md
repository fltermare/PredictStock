
# local test

```python
### main.py

flask_app = create_app('localtest')
# flask_app = create_app('development')
```

```sh
export FLASK_APP=wsgi
export FLASK_ENV=development
flask run
```


# production
```python
### main.py

# flask_app = create_app('localtest')
flask_app = create_app('development')
```