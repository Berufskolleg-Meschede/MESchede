## API-Endpoints used from the Azubi-ERP:
/inventory
GET to get the current inventory to tell if production can start
POST to insert new items into the inventory if there are new items

/article
GET to receive information about the articles

/order
GET to receive newest information about orders and how to execute them

## OPC UA integration

See [the current PLC handshake and offline testing guide](docs/opc-ua-integration.md).
An example production request is saved in `backend/examples/production-order.json`.
