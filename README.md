# Usage Instructions

## With docker
Install and run docker on your system (see www.docker.com/get-started)

Run `docker build -t hackernews .` to create the container in which the tool runs.

Run `docker run hackernews --posts x` to run the tool where `x` is the number of posts you wish to output to `STDOUT` (`0 < x <= 100`).

## Without docker
Install python and pip (see <pip.pypa.io/en/stable/installing/>).

Run `pip install requests validators` to install additional Python modules.

Run `python hackernews.py --posts x` where `x` is the number of posts you wish to output to `STDOUT` (`0 < x <= 100`).

# Modules
I used the following Python modules

## argparse
The argparse module handles parsing and some validation of command line arguments.  I have used it to store the value of the `--posts` argument and ensure that it is an integer.  This module also produces help text if incorrect arguments are used.

## collections
The collections module includes `OrderedDict` (an ordered dictionary).  This allowed me to control the order of the post elements in the output JSON.  The `json.dumps` method only supports no sorting or alphabetical sorting. 

## json
The json module contains a method `dumps` that prints a dictionary as JSON in a readable format.  I have used this when outputing the JSON.

## logging
The logging module contains easy to use logging infrastructure that is very useful for debugging.

## requests
The requests module is an easy to use library for basic HTTP requests.  I have used it to get JSON from the hackernews API.

## sys
The sys module contains the `exit` method that I have used for exiting early with error codes in critical error conditions.

## validators
The validators module contains a URL validator.  Under the hood this is just a regex checker, which I could have used directly in my code, however it is neater to use this module.

# Dockerfile notes

`FROM python:3` - use the Python 3 Docker base image

`ADD hackernews.py /` - copy in the Python script

`RUN pip install requests validators` - install additional modules

`ENTRYPOINT [ "python", "./hackernews.py" ]` - define hackernews script as the entrypoint.  This handled arguments better than `CMD`.

# Troubleshooting

Log are written to `hackernews.log`.  To retrieve logs from a docker container run `docker container ls -a` and identify the `CONTAINER ID` from which you want to retrieve logs.  Then run `docker cp <CONTAINER ID>:/hackernews.log <DESTINATION>` to copy the log file to `<DESTINATION>`.

# Issues
Unicode characters aren't output correctly.  For example: 
```
"title": "Actix-web \u2013 A small, pragmatic, and fast web framework for Rust",
```

Replacing 
```python
print(json.dumps(output_list, indent=4, separators=(',', ': ')))
```
with 
```python
print(json.dumps(output_list, ensure_ascii=False, indent=4, separators=(',', ': ')).encode('utf8'))
``` 
resolves the problem when running outside Docker.  However, Docker doesn't handle the output well and we see:

```
b'[\n    {\n        "title": "Actix-web \xe2\x80\x93 A small, pragmatic, and fast web framework for Rust",\n        "uri": "https://docs.rs/actix-web/1.0.0/actix_web",\n        "author": "Dowwie",\n        "points": 61,\n        "comments": 9,\n        "rank": 1\n    },\n    {\n        "title": "Firefox Monitor",\n        "uri": "https://monitor.firefox.com/scan",\n        "author": "madhukarah",\n        "points": 153,\n        "comments": 38,\n        "rank": 2\n    },\n    {\n        "title": "Writing a game engine in pure C: The Graphic Initialization",\n        "uri": "https://prdeving.wordpress.com/2019/06/05/how-to-write-a-game-engine-in-pure-c-part-2-the-graphic-initialization/",\n        "author": "buba",\n        "points": 52,\n        "comments": 10,\n        "rank": 3\n    }\n]'
```

At this time I have been unable to find a solution.
