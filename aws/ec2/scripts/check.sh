for f in $1; do
    pushd $f
    n=`../vsc | fgrep "Instance is not created" | wc -l`
    if [[ $n -gt 0 ]]; then
        echo "restarting $f because of $n"
        ../restart.sh &
    fi
    popd
done
