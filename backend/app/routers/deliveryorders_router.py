from fastapi import APIRouter
router = APIRouter(
    prefix="/deliveryorder",
    tags=["deliveryorder"]
)
@router.get("/")
def list_deliveryorders():
    """
    List all deliveryorders
    :return:All delivery orders"""

    raise NotImplementedError("Method not implemented yet.")
    #TODO: Implement getting all deliveryorders

@router.get("/{deliveryorder_id}")
def get_deliveryorder(deliveryorder_id: str):
    """
    Get a single deliveryorder
    :param deliveryorder_id: The id of the deliveryorder to get
    :return: The deliveryorder with the given id"""
    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement getting a single deliveryorder

@router.post("/")
def post_deliveryorder():
    """
    posts a single deliveryorder
    :return: status of operation
    """
    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement creating a new deliveryorder

@router.patch("/{deliveryorder_id}")
def patch_deliveryorder(deliveryorder_id: str):
    """
    updates a single deliveryorder by its id
    :param deliveryorder_id: the id of the deliveryorder to update
    :return: the updated deliveryorder
    """
    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement updating a deliveryorder

@router.delete("/{deliveryorder_id}")
def delete_deliveryorder(deliveryorder_id: str):
    """
    deletes a single deliveryorder by its id
    :param deliveryorder_id:
    :return: status of operation
    """
    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement deleting a deliveryorder