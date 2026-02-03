from fastapi import APIRouter
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

@router.post("/")
def post_productionorder():
    """
    posts a single productionorder
    :return: status of operation
    """
    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement creating a new productionorder

@router.patch("/{productionorder_id}")
def patch_productionorder(productionorder_id: str):
    """
    updates a single productionorder by its id
    :param productionorder_id: the id of the productionorder to update
    :return: the updated productionorder
    """
    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement updating a productionorder

@router.delete("/{productionorder_id}")
def delete_productionorder(productionorder_id: str):
    """
    deletes a single productionorder by its id
    :param productionorder_id:
    :return: status of operation
    """
    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement deleting a productionorder