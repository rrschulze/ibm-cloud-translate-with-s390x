#!/usr/bin/env python3

from flask import Flask, render_template, request
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.semconv.trace import SpanAttributes
import configparser
import requests
import wikipedia
import time
import random

# Read configuration

configparser = configparser.ConfigParser()
configparser.read('app.ini')

host = configparser['DEFAULT']['host']
app_service_port = configparser['DEFAULT']['app_service_port']
client_service_name = configparser['DEFAULT']['client_service_name']


# Set otel service name
resource = Resource(attributes={
    SERVICE_NAME: client_service_name
})

# Initialize tracing and an exporter
provider = TracerProvider(resource=resource) 
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)


def call_app_service(input_sentence):
    output_sentence = ""
        
    with tracer.start_as_current_span("identify_and_translate(): call translate service") as span:
        url = "http://app-service:" + app_service_port+ "/api/translate"
        response = requests.post(url=url,params={'input_sentence':input_sentence})

        output_sentence = response.text
        
        current_span=trace.get_current_span()
        current_span.set_attribute("output_sentence=", output_sentence)
    
    return(output_sentence)   

def main():
    while (True):
        try:
            summary = ""
            with tracer.start_as_current_span("main(): call wiki") as span:
                result = wikipedia.random()

                search = wikipedia.search(result)

                summary = wikipedia.summary(search[0])

                if len(summary) > 100:
                    summary = summary.partition('.')[0] + '.'
                print(summary)
            
            with tracer.start_as_current_span("main(): call translation") as span:
                translation = call_app_service(summary)
                print(translation)
                current_span=trace.get_current_span()
                current_span.set_attribute("summary", summary)
                current_span.set_attribute("translation", translation)
                time.sleep(random.randint(0,10))
        except:
            print("failed search")




if __name__ == "__main__":
    main()