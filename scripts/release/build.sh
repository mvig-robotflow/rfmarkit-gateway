cd ../cvt_measurement || exit
python setup.py bdist_wheel

cd ../tcpbroker || exit
python setup.py bdist_wheel

cd ../release || exit

mv ../cvt_measurement/dist/* ./
mv ../tcpbroker/dist/* ./

rm -rf ../cvt_measurement/build
rm -rf ../cvt_measurement/dist
rm -rf ../cvt_measurement/*.egg-info

rm -rf ../tcpbroker/build
rm -rf ../tcpbroker/dist
rm -rf ../tcpbroker/*.egg-info