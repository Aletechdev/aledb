echo "Downloading: $1"
sudo azcopy copy "https://aledata.blob.core.windows.net/output/$1?sv=2021-10-04&spr=https%2Chttp&st=2024-09-25T02%3A30%3A40Z&se=2034-09-26T02%3A30%3A00Z&sip=4.231.249.59&sr=c&sp=racwdxltf&sig=3%2BPAEm9KFgghlDOos%2FGhD7PV21%2BhHLIu7srNZMXwVmM%3D" '.' --recursive=true

echo "extracting..."
sudo find $1 -name '*.tar.gz' -execdir tar -xzvf '{}' \;

sudo rm $1/*.tar.gz

#scp -i /home/wumuyao1996/.ssh/muyao -r $1/* wmuyao@aledb.ucsd.edu:/data/aledata/

echo "filtering..."
sudo python3 ~/preuploader/filter.py $1/*/*

sudo mv $1 /data/aledata

sudo docker exec -it aledb-web python manage.py upload /data/aledata/$1
echo "sudo docker exec -it aledb-web python manage.py upload /data/aledata/$1"
