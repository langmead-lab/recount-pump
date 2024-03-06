#!/bin/bash
dir=$(dirname $0)

#SIRV-1
#wget https://www.lexogen.com/wp-content/uploads/2018/08/SIRV_Set1_Sequences_170612a-ZIP.zip
#wget https://www.lexogen.com/wp-content/uploads/2017/05/SIRV_Sequences_151124.zip
#wget https://www.lexogen.com/wp-content/uploads/2018/08/SIRV_Set1_Lot00141_Sequences_170612a-ZIP.zip

#SIRV-2
#wget https://www.lexogen.com/wp-content/uploads/2018/08/SIRV_Set2_Sequences_170612a-ZIP.zip
#wget https://www.lexogen.com/wp-content/uploads/2018/08/SIRV_Set2_Lot001484_Sequences_170612a-ZIP.zip
#wget https://www.lexogen.com/wp-content/uploads/2018/08/SIRV_Set2_Lot001603_Sequences_170612a.zip

#SIRV-3
#wget https://www.lexogen.com/wp-content/uploads/2018/08/SIRV_Set3_Sequences_170612a-ZIP.zip
#wget https://www.lexogen.com/wp-content/uploads/2018/08/SIRV_Set3_Lot001485_Sequences_170612a-ZIP.zip
#wget https://www.lexogen.com/wp-content/uploads/2018/08/SIRV_Set3_Lot001492_Sequences_170612a-ZIP.zip
#wget https://www.lexogen.com/wp-content/uploads/2018/08/SIRV_Set3_Lot001602_Sequences_170612a.zip

rm -rf SIRV* *ZIP* *.zip
for i in $(grep '^http.*zip$' $dir/README.md) ; do
    f0=$(basename $i)
    curl "${i}" > ${f0}
    unzip ${f0}
done
