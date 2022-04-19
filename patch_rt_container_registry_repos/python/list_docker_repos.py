import sys
import requests
from urllib.parse import urljoin

JFROG_API_KEY_HEADER_NAME = 'X-JFrog-Art-Api'


class DockerRegistryPagination:
    def __init__(self, concatenating_key):
        self.concatenating_key = concatenating_key

    def __call__(self, url, *args, **kwargs):
        response = requests.get(url, *args, **kwargs)
        response.raise_for_status()
        concatenated_list = response.json().get(self.concatenating_key, [])
        while 'next' in response.links.keys():
            url = urljoin(url, response.links['next']['url'])
            response = requests.get(url, *args, **kwargs)
            response.raise_for_status()
            concatenated_list.extend(response.json().get(self.concatenating_key, []))
        return concatenated_list


class ArtifactoryIntegrationLogic:
    def __init__(self, base_url, api_key, default_repo=None, username=None):
        self.username = username
        self.base_url = base_url
        if not self.base_url.startswith('https://'):
            self.base_url = 'https://' + base_url

        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]

        self.api_key = api_key
        self.default_repo = default_repo

    def get_artifactory_headers(self):
        return {
            JFROG_API_KEY_HEADER_NAME: self.api_key,
        }

    def _get_all_repos_data(self):
        res = requests.get(
            self.base_url + '/artifactory/api/repositories',
            headers=self.get_artifactory_headers(),
        )

        if res.status_code != 200:
            if res.status_code == 403:
                raise Exception(
                    'Artifactory token is not valid or has been revoked.'
                )

            raise Exception(
                f'Failed to get repositories. '
                f'Error: {res.text}. Code {res.status_code}'
            )

        return res.json()

    def list_repos(self, search=''):
        all_repos_data = self._get_all_repos_data()
        return sorted([i['key'] for i in all_repos_data if search.lower() in i['key'].lower()])

    def get_repo_type(self, repo_name):
        all_repos_data = self._get_all_repos_data()

        for i in all_repos_data:
            if i['key'] == repo_name:
                return i['packageType']

        raise Exception(
            f'Repository {repo_name} does not exist or user does not have permissions for it.'
        )

    def _list_docker_folders(self, repo, search=''):
        request_func = DockerRegistryPagination('repositories')
        try:
            repos = request_func(
                self.base_url + '/artifactory/api/docker/%s/v2/_catalog' % repo,
                headers=self.get_artifactory_headers(),
            )
            return [i for i in repos if search.lower() in i.lower()]
        except requests.exceptions.HTTPError as exc:
            raise Exception(
                f'Failed to get images list using docker catalog. '
                f'Error: {exc.response.text}. Code {exc.response.status_code}'
            ) from exc

    def list_folders(self, repo=None, search=''):
        if not repo:
            repo = self.default_repo

        if not repo:
            raise ValueError('Either send a repo or set the default repo for this to work.')

        folders = self._list_docker_folders(repo, search)
        return sorted(folders)

    def _list_docker_images(self, folder, repo, search=''):
        request_func = DockerRegistryPagination('tags')
        try:
            tags = request_func(
                self.base_url + '/artifactory/api/docker/%s/v2/%s/tags/list' % (repo, folder),
                headers=self.get_artifactory_headers()
            )
            return [i for i in tags if search.lower() in i.lower()]
        except requests.exceptions.HTTPError as exc:
            raise Exception(
                f'Failed to get tag list using docker catalog. '
                f'Error: {exc.response.text}. Code {exc.response.status_code}'
            ) from exc

    def list_images(self, folder='', repo=None, search=''):
        if not repo:
            repo = self.default_repo

        if not repo:
            raise ValueError('Either send a repo or set the default repo for this to work.')

        images = self._list_docker_images(folder, repo, search)
        return sorted(images)


rt_domain = sys.argv[1]
api_key = sys.argv[2]
user = sys.argv[3]
with open("images.csv", "w") as outfile:
    rt = ArtifactoryIntegrationLogic(f"https://{rt_domain}", api_key, username=user)
    repositories = rt.list_repos()
    for repository in repositories:
        repo_type = rt.get_repo_type(repository).lower()
        if repo_type == "docker":
            repo_folders = rt.list_folders(repo=repository)
            for repo_folder in repo_folders:
                folder_images = rt.list_images(repo=repository, folder=repo_folder)
                for folder_image in folder_images:
                    outfile.write(f"{repository}, {repo_folder}, {folder_image}\r\n")
