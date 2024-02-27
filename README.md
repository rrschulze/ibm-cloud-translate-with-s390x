# Translate with s390x and ibm cloud
Use this repositroy to run a simple translator application to demonstrate distributed tracing with OpenTelemetry.

## Create VM on s390x
Follow the instructions in the [README.md](https://github.com/rrschulze/ibm-cloud-s390x-single-vm/) of repository [ibm-cloud-s390x-single-vm](https://github.com:/rrschulze/ibm-cloud-s390x-single-vm) to create a virtual machine with linux/s390x architecture on IBM Cloud.

## Run Translator application on vsi-s390x-01
1. Open a new terminal window
2. `ssh -l labuser <ipv4_address>`
3. `git clone https://github.com/rrschulze/ibm-cloud-translate-with-s390x`
4. `cd ~/ibm-cloud-translate-with-s390x/translator`
5. `vim app.ini` and add the Language Translator API key and URL
- `api_key=<api key>`
- `api_url=<url>`
6. (optional) Specify a different target language for the translation by modifying these two parameters:
- `model_id=en-pl`
- `target_language=pl`
7. `chmod 744 ./run.sh`
8. `./run.sh`
9. Verify containers are up with `sudo docker ps`