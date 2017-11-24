Bootstrap: docker
From: benlangmead/star

%post

    cat >/home/biodocker/bin/star <<'EOF'
#!/bin/sh
if [ "${1}" = "long" ] ; then
   shift
   /home/biodocker/bin/STARlong $@
else
   /home/biodocker/bin/STAR $@
fi
EOF
    chmod a+x /home/biodocker/bin/star
    mkdir -p /home1 /work /scratch  # for stampede 2

%runscript

    exec /home/biodocker/bin/star "$@"
