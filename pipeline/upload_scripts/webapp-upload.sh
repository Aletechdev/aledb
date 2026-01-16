echo "Downloading: $1"
#sudo cp -r "/output/$1" '.'
sudo mkdir /data/aledata/$1
echo "extracting..."
sudo find /output/$1 -name '*.tar.gz' -execdir tar -xzvf '{}' -C "/data/aledata/$1" \;

#scp -i /home/wumuyao1996/.ssh/muyao -r $1/* wmuyao@aledb.ucsd.edu:/data/aledata/

#echo "filtering..."
#sudo python3 ~/preuploader/filter.py $1/*/*

sudo docker exec aledb-web python manage.py upload /data/aledata/$1
echo "sudo docker exec aledb-web python manage.py upload /data/aledata/$1"
