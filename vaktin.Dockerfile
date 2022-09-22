FROM python:3.6-slim
RUN pip install beautifulsoup4
RUN pip install pandas
RUN pip install dash
RUN pip install dash_bootstrap_components
RUN apt-get clean && apt-get update && apt-get install -y locales
RUN locale-gen is_IS.UTF-8
RUN sed -i -e 's/# is_IS.UTF-8 UTF-8/is_IS.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
ENV LANG is_IS.UTF-8  
ENV LANGUAGE is_IS:en  
ENV LC_ALL is_IS.UTF-8 
COPY . .
EXPOSE 8000
ENTRYPOINT [ "python", "vaktin_gui.py"]