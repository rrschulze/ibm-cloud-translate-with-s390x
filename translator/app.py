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


# Read configuration

configparser = configparser.ConfigParser()
configparser.read('app.ini')

host = configparser['DEFAULT']['host']
app_service_port = configparser['DEFAULT']['app_service_port']
identify_service_port = configparser['DEFAULT']['identify_service_port']
translate_service_port = configparser['DEFAULT']['translate_service_port']

app_service_name = configparser['DEFAULT']['app_service_name']

model_id = configparser['DEFAULT']['model_id']
target_language = configparser['DEFAULT']['target_language']

# Create app
app = Flask(__name__)

# Set otel service name
resource = Resource(attributes={
    SERVICE_NAME: app_service_name
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

@app.route("/")
def index():
    with tracer.start_as_current_span("index()") as span:
        return render_template("./index.html")



def identify_and_translate(input_sentence):
    model = model_id
    output_sentence = ""
    target = target_language
    

    with tracer.start_as_current_span("identify_and_translate() call identify service") as span:
        url = "http://identify-service:" + identify_service_port+ "/api/identify"
        response = requests.post(url=url,params={'input_sentence':input_sentence})

        language = response.text
        
        current_span=trace.get_current_span()
        current_span.set_attribute("language=", language)

        if language!=None and language!="":
            model = language+"-"+target
        
        current_span.set_attribute("model=", model)

    with tracer.start_as_current_span("identify_and_translate(): call translate service") as span:
        url = "http://translate-service:" + translate_service_port+ "/api/translate"
        response = requests.post(url=url,params={'input_sentence':input_sentence,'language_model':model})

        output_sentence = response.text
        
        current_span=trace.get_current_span()
        current_span.set_attribute("output_sentence=", output_sentence)
    
    return(output_sentence)



@app.route("/api/translate", methods=["POST"])
def process_api_request():
    model = model_id
    output_sentence = ""
    target = target_language

    with tracer.start_as_current_span("process_api_request()") as span:
        with tracer.start_as_current_span("process_request(): POST /api/translate") as span:
            current_span=trace.get_current_span()
            current_span.set_attribute(SpanAttributes.HTTP_METHOD, "POST")
            current_span.set_attribute(SpanAttributes.HTTP_URL, "http://"+host+":"+app_service_port+"/api/translate")  
        
            # Get input sentence
            with tracer.start_as_current_span("process_api_request(): get input_sentence") as span:
                input_sentence = request.args.get("input_sentence")

                current_span.set_attribute("input_sentence=", input_sentence)
                current_span.set_attribute("model=", model)

            output_sentence=identify_and_translate(input_sentence=input_sentence)

            return output_sentence


@app.route("/translate", methods=['GET',"POST"])
def process_request():
    model = model_id
    output_sentence = ""
    target = target_language

    with tracer.start_as_current_span("process_request()") as span:
        if request.method == "GET":
            with tracer.start_as_current_span("process_request(): GET /translate") as span:
                current_span=trace.get_current_span()
                current_span.set_attribute(SpanAttributes.HTTP_METHOD, "GET")
                current_span.set_attribute(SpanAttributes.HTTP_URL, "http://"+host+":"+app_service_port+"/translate")  
                #chat_history.append(msg)

                chat_history.append(" ")

                history_copy = chat_history.copy()
                history_copy.reverse()

                return render_template("./translate.html", messages=history_copy)
        else:
            with tracer.start_as_current_span("process_request(): POST /translate") as span:
                current_span=trace.get_current_span()
                current_span.set_attribute(SpanAttributes.HTTP_METHOD, "POST")
                current_span.set_attribute(SpanAttributes.HTTP_URL, "http://"+host+":"+app_service_port+"/translate")  
            
                # Get input sentence
                with tracer.start_as_current_span("process_request(): get form input") as span:
                    input_sentence = request.form.get("input")
                    current_span=trace.get_current_span()
                    current_span.set_attribute("input_sentence=", input_sentence)
                    current_span.set_attribute("model=", model)

                output_sentence = identify_and_translate(input_sentence=input_sentence)

                with tracer.start_as_current_span("process_request(): prepare output") as span:
                    chat_history = []
                    current_span=trace.get_current_span()
                    chat_history.append(str(output_sentence))
                    chat_history.append("# " + input_sentence)

                    history_copy = chat_history.copy()
                    history_copy.reverse()

                return render_template("./translate.html", messages = history_copy)

if __name__ == "__main__":
    app.run(host=host, port=app_service_port, debug=True, threaded=False)
#    app.run(ssl_context='adhoc')