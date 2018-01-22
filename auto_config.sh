FWDIR="$(cd `dirname $0`/../; pwd)"

TOP=$FWDIR
ENV=${TOP##/*/env/}
ENV=${ENV%%/apps}

cd $TOP/config

echo "Auto config for ENV: $ENV, TOP: $TOP"
python config_rep.py --config template.json --econfig envs.json --env $ENV --top $TOP --verbose
