# README #

### Operation ###

* This server expects calibration instructions, sent by the tergite-calibration-supervisor.
* Currently operates only on Qblox instruments

### Run it ###
On a computer that is on the same local network with the cluster go to the cloned repo directory and start it as
`.\start_uvicorn.ps1`

### To find the `dns` name ###
run `ipconfig /all`  to find the IPv4 address.
run `nslookup <IPv4>`  to find the DNS name.
