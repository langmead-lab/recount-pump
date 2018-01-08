#!/bin/sh

for i in `find -name gtf | sed 's/^\.\///' | sed 's/\/.*//'` ; do
    cat >.$i.upload.sh <<EOF
#!/bin/bash -l
#SBATCH
#SBATCH --job-name=upload_${i}
#SBATCH --partition=parallel
#SBATCH --output=.$i.upload.sh.o
#SBATCH --error=.$i.upload.sh.e
#SBATCH --nodes=1
#SBATCH --mem=1G
#SBATCH --partition=shared
#SBATCH --time=8:00:00
sh synapse_upload.sh $i
EOF
    echo "sbatch .$i.upload.sh"
done
