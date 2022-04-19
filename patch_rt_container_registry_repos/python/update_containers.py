import sys
import csv
import subprocess

rt_domain = sys.argv[1]
api_key = sys.argv[2]
user = sys.argv[3]
with open('images.csv', 'r', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    rows = enumerate(reader)
    try:
        for line_num, row in rows:
            if len(row) != 3:
                raise Exception('Malformed line #{}, expecting 3 fields, length was: {}'.format(line_num, len(row)))
            (repo_name, image_name, image_tag) = row
            repo_name = repo_name.strip()
            image_name = image_name.strip()
            image_tag = image_tag.strip()
            if not repo_name or not image_name or not image_tag:
                raise Exception(f"One of the fields is empty. "
                                f"Repo:'{repo_name}', Image:'{image_name}', Tag:'{image_tag}'")

            cmdline = f'./update_container_image.sh ' \
                      f'"{user}" "{api_key}" "{rt_domain}" "{repo_name}" "{image_name}" "{image_tag}"'
            print(f'Processing image: {image_name}:{image_tag} from repository {repo_name}')
            with subprocess.Popen(
                    cmdline,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
            ) as process:
                stdout, stderr = process.communicate()
                return_code = process.returncode
                stdout = stdout.decode()
                stderr = stderr.decode()
                if return_code != 0:
                    print(f"Failed to run: {cmdline}. Error code: {return_code}, stderr: {stderr}, stdout: {stdout}")
                    continue

    except ValueError as e:
        raise Exception('Exception processing csv line #{}'.format(reader.line_num, str(e)))
