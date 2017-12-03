FROM python:3.6

RUN mkdir /fourchon
COPY *.py requirements.txt /fourchon/
RUN pip install -r fourchon/requirements.txt

ENTRYPOINT ["python3", "/fourchon/main.py"]