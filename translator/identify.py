#!/usr/bin/env python3

from flask import Flask, render_template, request
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.semconv.trace import SpanAttributes
from ibm_watson import LanguageTranslatorV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import configparser
import json


# Read configuration

configparser = configparser.ConfigParser()
configparser.read('app.ini')

host = configparser['DEFAULT']['host']
identify_service_port = configparser['DEFAULT']['identify_service_port']

identify_service_name = configparser['DEFAULT']['identify_service_name']

api_key = configparser['DEFAULT']['api_key']
api_url = configparser['DEFAULT']['api_url']
model_id = configparser['DEFAULT']['model_id']

# Create app
app = Flask(__name__)

# Set otel service name
resource = Resource(attributes={
    SERVICE_NAME: identify_service_name
})

# Initialize tracing and an exporter
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# Initialize automatic instrumentation with Flask
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

chat_history = []


@app.route("/healthcheck", methods=['GET'])
@tracer.start_as_current_span("/healthcheck")
def healthcheck():
    return __name__

@app.route("/api/identify", methods=["POST"])
def translate():
        with tracer.start_as_current_span("POST /api/identify") as span:
            input_sentence = request.args.get("input_sentence")
            language = ""

            current_span=trace.get_current_span()
            current_span.set_attribute(SpanAttributes.HTTP_METHOD, "POST")
            current_span.set_attribute(SpanAttributes.HTTP_URL, "http://"+host+":"+ identify_service_port+"/api/identify")  

            print("input_sentence=", input_sentence)

            with tracer.start_as_current_span("Call translator") as span:
                current_span=trace.get_current_span()
                current_span.set_attribute("input_sentence=", input_sentence)

                response = None

               # try:
                    # Prepare the Authenticator
                authenticator = IAMAuthenticator(api_key)
                language_translator = LanguageTranslatorV3(
                    version='2018-05-01',
                    authenticator=authenticator
                )

                language_translator.set_service_url(api_url )

                # Identify
                response = language_translator.identify(text=input_sentence)

                print(response)

                probability = 0
                language = ""

                for lang in response.result["languages"]:
                    p = lang["confidence"]
                    if (p > probability):
                        probability = p
                        l = lang["language"]
                    
                language = l
                    
                print("language=",language)
                print("probability", probability)
                current_span.set_attribute("language=", language)
                current_span.set_attribute("probability=", probability)
            #    except:
            #        print("Execption!")
            #        current_span.set_status("Failed")
        return language

if __name__ == "__main__":
    app.run(host=host, port=identify_service_port, debug=True, threaded=False)
#    app.run(ssl_context='adhoc')