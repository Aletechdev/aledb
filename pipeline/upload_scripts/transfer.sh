: "${AZURE_OUTPUT_CONTAINER_SAS:?Set AZURE_OUTPUT_CONTAINER_SAS (source /upload/.azure-env)}"

echo "Downloading: $1"
sudo -E azcopy copy "https://aledata.blob.core.windows.net/output/$1?${AZURE_OUTPUT_CONTAINER_SAS}" '.' --recursive=true

echo "extracting..."
sudo find $1 -name '*.tar.gz' -execdir tar -xzvf '{}' \;

sudo rm $1/*.tar.gz

#scp -i /home/wumuyao1996/.ssh/muyao -r $1/* wmuyao@aledb.ucsd.edu:/data/aledata/

echo "filtering..."
sudo python3 ~/preuploader/filter.py $1/*/*

sudo mv $1 /data/aledata

sudo docker exec -it aledb-web python manage.py upload /data/aledata/$1
echo "sudo docker exec -it aledb-web python manage.py upload /data/aledata/$1"
