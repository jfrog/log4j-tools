username=$1
password=$2
rt_domain=$3
repo_name=$4
image_name=$5
tag=$6

export CI=true
jf rt docker-pull --user=$username --password=$password --url=https://$rt_domain $rt_domain/$repo_name/$image_name:$tag $rt_domain

echo "from $rt_domain/$repo_name/$image_name:$tag" > /tmp/Dockerfile
echo "ENV LOG4J_FORMAT_MSG_NO_LOOKUPS=true" >> /tmp/Dockerfile

docker build -t $rt_domain/$repo_name/$image_name:$tag - < /tmp/Dockerfile
docker push $rt_domain/$repo_name/$image_name:$tag
