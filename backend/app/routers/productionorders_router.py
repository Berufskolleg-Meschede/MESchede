from fastapi import APIRouter, status
from opcua import ua, Client
from ..workers.production_queue import ProductionOrderPayload, order_queue
from ..clients.opc_ua_client import OpcUaClient
from dotenv import load_dotenv
from os import environ

router = APIRouter(
    prefix="/productionorder",
    tags=["productionorder"]
)
@router.get("/")
def list_productionorders():
    """
    List all productionorders
    :return:All production orders"""

    raise NotImplementedError("Method not implemented yet.")
    #TODO: Implement getting all productionorders

@router.get("/{productionorder_id}")
def get_productionorder(productionorder_id: str):
    """
    Get a single productionorder
    :param productionorder_id: The id of the productionorder to get
    :return: The productionorder with the given id"""

    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement getting a single productionorder

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def post_productionorder(payload: ProductionOrderPayload):
    """
    posts a single productionorder
    :return: status of operation
    """

    load_dotenv()

    opc_client = OpcUaClient(url=environ.get("OPC_UA_URL"))
    await opc_client.connect()
    auftragssteuerung_node_id = environ.get("AUFTRAGSSTEUERUNG_NODE_ID")
    mes_status_node_id = environ.get("STATUS_NODE_ID")
    mes_status_node = opc_client.client.get_node(mes_status_node_id)
    auftragssteuerung_node = opc_client.client.get_node(auftragssteuerung_node_id)
    print("NodeClass:", auftragssteuerung_node.get_node_class())
    print("DataType:", auftragssteuerung_node.get_data_type_as_variant_type())
    print("Access:", auftragssteuerung_node.get_access_level(), auftragssteuerung_node.get_user_access_level())
    dv = ua.DataValue(
    ua.Variant(1, ua.VariantType.Byte)
    )

    auftragssteuerung_node.get_child()

    try:   
        # node.set_data_value(dv)
        print(auftragssteuerung_node.get_data_value().Value.Value)
    except Exception as e:
        print(f"Error setting value on OPC UA server: {e}")
    await opc_client.disconnect()
    
    ## await order_queue.put(payload)
    # return {
    #    "queued": True,
    #    "order_id": payload.order_id,
    #    "queue_size": order_queue.qsize(),
    #}

@router.patch("/{productionorder_id}")
async def patch_productionorder(productionorder_id: str):
    """
    updates a single productionorder by its id
    :param productionorder_id: the id of the productionorder to update
    :return: the updated productionorder
    """
    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement updating a productionorder

@router.delete("/{productionorder_id}")
async def delete_productionorder(productionorder_id: str):
    """
    deletes a single productionorder by its id
    :param productionorder_id:
    :return: status of operation
    """
    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement deleting a productionorder