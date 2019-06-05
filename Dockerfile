FROM python:3
ADD hackernews.py /
RUN pip install requests validators
ENTRYPOINT [ "python", "./hackernews.py" ]