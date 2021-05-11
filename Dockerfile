FROM python:3.9

RUN pip install pandas tqdm requests xlrd openpyxl xlsxwriter python-decouple beautifulsoup4 fhir.resources python-keycloak pronto Owlready2 tqdm

RUN mkdir /scripts
COPY ./ /scripts

WORKDIR /scripts

ENTRYPOINT bash