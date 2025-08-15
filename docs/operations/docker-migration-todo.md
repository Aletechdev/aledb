# Docker Data Migration to 1TB Disk - TODO

## Overview
Migrate Docker data from the full root filesystem (85GB usage) to the unmounted 1TB disk (`/dev/sda1`) to resolve disk space issues.

## Current Situation
- Root filesystem (`/dev/root`): 124G total, 124G used, 288M available (100% full)
- Docker consuming: 85GB in `/var/lib/docker`
- Available 1TB disk: `/dev/sda1` (unmounted)

## Prerequisites
- [ ] Backup any critical data
- [ ] Ensure you have sudo access
- [ ] Stop any running Docker containers before starting

---

## Step 1: Prepare the 1TB Disk

### 1.1 Check Current Disk Status
```bash
# Verify the disk exists and check current filesystem
sudo blkid /dev/sda1
lsblk /dev/sda
```

### 1.2 Create Filesystem (if needed)
```bash
# If blkid shows no filesystem, create ext4 filesystem
sudo mkfs.ext4 /dev/sda1
```

### 1.3 Create Mount Point
```bash
# Create directory for mounting the 1TB disk
sudo mkdir -p /mnt/docker-data
```

### 1.4 Mount the Disk
```bash
# Mount the 1TB disk
sudo mount /dev/sda1 /mnt/docker-data

# Verify mount successful
df -h /mnt/docker-data
```

---

## Step 2: Stop Docker Services

### 2.1 Stop Docker Compose Services
```bash
# Navigate to your docker-compose directory
cd /path/to/your/docker-compose/directory

# Stop all services
sudo docker-compose down
```

### 2.2 Stop Docker Daemon
```bash
sudo systemctl stop docker
```

### 2.3 Verify Docker is Stopped
```bash
sudo systemctl status docker
# Should show "inactive (dead)"
```

---

## Step 3: Migrate Docker Data

### 3.1 Copy Docker Data to New Location
```bash
# Copy all Docker data to the 1TB disk (this may take several minutes)
sudo rsync -av /var/lib/docker/ /mnt/docker-data/
```

### 3.2 Backup Original Docker Directory
```bash
# Rename original directory as backup
sudo mv /var/lib/docker /var/lib/docker.backup
```

### 3.3 Create Symbolic Link
```bash
# Create symlink to new location
sudo ln -s /mnt/docker-data /var/lib/docker
```

### 3.4 Verify Symlink
```bash
ls -la /var/lib/docker
# Should show: /var/lib/docker -> /mnt/docker-data
```

---

## Step 4: Make Mount Permanent

### 4.1 Get Disk UUID
```bash
# Get the UUID of the 1TB disk
UUID=$(sudo blkid /dev/sda1 -o value -s UUID)
echo "UUID: $UUID"
```

### 4.2 Add to /etc/fstab
```bash
# Add permanent mount entry
echo "UUID=$UUID /mnt/docker-data ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
```

### 4.3 Test fstab Entry
```bash
# Test the fstab entry
sudo umount /mnt/docker-data
sudo mount -a
df -h /mnt/docker-data
# Should show the disk mounted again
```

---

## Step 5: Start Docker and Test

### 5.1 Set Correct Permissions
```bash
# Ensure proper ownership and permissions
sudo chown -R root:root /mnt/docker-data
sudo chmod 755 /mnt/docker-data
```

### 5.2 Start Docker Daemon
```bash
sudo systemctl start docker
```

### 5.3 Verify Docker Status
```bash
sudo systemctl status docker
sudo docker info
```

### 5.4 Start Your Services
```bash
# Navigate to your docker-compose directory
cd /path/to/your/docker-compose/directory

# Start your services
sudo docker-compose up -d

# Check services are running
sudo docker-compose ps
```

---

## Step 6: Verification and Cleanup

### 6.1 Verify Space Usage
```bash
# Check root filesystem space (should show significant improvement)
df -h /

# Check new Docker location
df -h /mnt/docker-data

# Verify Docker data is in new location
sudo du -sh /mnt/docker-data
```

### 6.2 Test Application Functionality
- [ ] Test your web application
- [ ] Check database connections
- [ ] Verify all services are working correctly

### 6.3 Clean Up (Only After Verification)
```bash
# Remove the backup ONLY after confirming everything works
sudo rm -rf /var/lib/docker.backup
```

---

## Rollback Plan (If Needed)

If something goes wrong, here's how to rollback:

### Rollback Steps
```bash
# Stop Docker
sudo systemctl stop docker

# Remove symlink
sudo rm /var/lib/docker

# Restore from backup
sudo mv /var/lib/docker.backup /var/lib/docker

# Remove fstab entry
sudo sed -i '/mnt\/docker-data/d' /etc/fstab

# Unmount the disk
sudo umount /mnt/docker-data

# Start Docker
sudo systemctl start docker
```

---

## Expected Results

After completion:
- Root filesystem usage should drop from ~100% to ~70-75%
- Docker data will be on 1TB disk with plenty of room to grow
- All existing containers, images, and volumes preserved
- System will be stable and have room for logs and updates

---

## Notes

- The migration process preserves all existing Docker data
- No need to rebuild containers or re-download images
- The 1TB disk will auto-mount on system reboot
- Monitor disk usage regularly: `df -h` and `docker system df`

## Estimated Time
- Total process: 30-60 minutes
- Data copy time depends on Docker data size (85GB ≈ 10-30 minutes)
