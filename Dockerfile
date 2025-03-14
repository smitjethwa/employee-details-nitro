FROM public.ecr.aws/lts/amazonlinux:latest
RUN yum install -y python3 pip
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
CMD ["python3", "app.py"]
