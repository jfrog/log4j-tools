# patch_rt_container_registry_repos

A patch tool to mitigate container images managed in Artifactory from log4shell.
### Note that the patch is relevant only for log4J versions 2.10.0 or newer.

The tool adds a layer to every selected container images maintained inside Artifactory container registry repositories with environment variable that disabled log4j remote calls (LOG4J_FORMAT_MSG_NO_LOOKUPS).


##### Usage

Update dependencies:
pip3 install -r requirements.txt

Two-Phase Flow:
1. Create a list of container images to patch:

```
python3 list_docker_repos.py "<rt_domain>" "<rt_api_key>" "<rt_username>"
```
This will create a file named images.csv. You can open the file in Excel, filter the list to your liking and save it back to images.csv.

Alternatively, create a file named images.csv containing a list of container images to patch using 3 columns in each line:
<repository_name>, <image_name>, <image_tag>

2. Patch the list of container images

```
python3 update_containers.py "<rt_domain>" "<rt_api_key>" "<rt_username>"
```
