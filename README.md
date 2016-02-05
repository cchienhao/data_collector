# Data Collector.
=====
## Source code structure
```
Root:
   data_collector
        doc         --   project doc--ocuments.
        scripts     --   launch or testing scripts
        spec        --   packagedoc--ec files.
        src         --   source code

Service:
        src/{service}/handler.py   --   Our Restful API request handler.
        src/{service}/service.py   --   Third party service API request client.
        src/{service}/staus.py     --   Special API status code
```


## How to add a new service under data_collector:
* Add your new module to enable and third-party authorization service configuration: 
```

$ vim src/conf/env_common.conf

...

enabled_modules: [
        ‘src.collectors.fitbit’,
        …
        ‘{src.collectors.{new_service_name}}’]

...
{new_service_name} : {
        redirect_uri: ‘{uri}’,
        consumer_key: ‘{client_id}’,
        client_id:: ‘{clientnt_id}’
        client_key: ‘{client_key}’,
        scope: ‘{app_scope}’
}
```

* Implement handler.py, service.py, under data_collector/src/{new_service_name}.

======
## Environment Setup
* $sudo apt-get update
* $sudo apt-get install python
* $sudo apt-get install python-dev
* $sudo apt-get -y install python-pip
* $sudo apt-get install redis
* $sudo pip install --upgrade pip
* $sudo pip install --upgrade virtualenv

## Install Redis
* sudo apt-add-repository ppa:chris-lea/redis-server
* sudo apt-get update
* sudo apt-get install redis-server

## Development Environment Setup
=======
* $git clone git@github.com:cchienhao/data_collector.git
* $cd data_collector
* $virtualenv venv
* $source venv/bin/activate
* $pip install -r src/res/requirements.txt

## Launch Command
* $PYTHONPATH=./src/collectors:./src/collectors/fitbit:./:./src:./src/common python src/core/api.py
