# # Robots & Rail
# for i in 100
# do
#   echo 192.168.44.$i
#   scp -rq /home/it/Desktop/g2/g2core/bin/pm-robot/g2core.bin  pi@192.168.44.$i:~/firmware-robot.bin
#   scp -rq /home/it/Desktop/g2/g2core/bin/pm-rail/g2core.bin  pi@192.168.44.$i:~/firmware-rail.bin
#   ssh pi@192.168.44.$i "sudo systemctl stop rpi.service"
#   ssh pi@192.168.44.$i './arduino-cli upload -p `readlink -f /dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.1:1.0` --fqbn arduino:sam:arduino_due_x --input-file firmware-robot.bin'
#   ssh pi@192.168.44.$i './arduino-cli upload -p `readlink -f /dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.2:1.0` --fqbn arduino:sam:arduino_due_x --input-file firmware-robot.bin'
#   ssh pi@192.168.44.$i './arduino-cli upload -p `readlink -f /dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.4:1.0` --fqbn arduino:sam:arduino_due_x --input-file firmware-rail.bin'
#   ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
# done


# # Stations
for i in 102 108 #{101..110}
do
  echo 192.168.44.$i
  ssh pi@192.168.44.$i "sudo systemctl stop rpi.service"
  scp -rq /home/it/Desktop/g2/g2core/bin/pm-station/g2core.bin  pi@192.168.44.$i:~/firmware.bin
  ssh pi@192.168.44.$i "./arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin"
  ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
done

# # Feeders
# for i in 21
# do
#   echo 192.168.44.$i
#   ssh pi@192.168.44.$i "sudo systemctl stop rpi.service"
#   scp -rq /home/it/Desktop/g2/g2core/bin/pm-feeder/g2core.bin  pi@192.168.44.$i:~/firmware-holder.bin
#   ssh pi@192.168.44.$i './arduino-cli upload -p `readlink -f /dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.4:1.0` --fqbn arduino:sam:arduino_due_x --input-file firmware-holder.bin'
#   # scp -rq /home/it/Desktop/g2/g2core/bin/pm-feeder-dosing/g2core.bin  pi@192.168.44.$i:~/firmware-dosing.bin
#   # ssh pi@192.168.44.$i './arduino-cli upload -p `readlink -f /dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.2:1.0` --fqbn arduino:sam:arduino_due_x --input-file firmware-dosing.bin'
#   ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
# done
