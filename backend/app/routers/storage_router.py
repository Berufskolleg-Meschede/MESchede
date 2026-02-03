from fastapi import APIRouter
router = APIRouter(
    prefix="/storage",
    tags=["storage"]
)

@router.get("/")
def list_storage():
    """
    lists the entire storage
    :return: storage
    """
    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement listing storage

@router.get("/{item_id}")
def get_storage(item_id: str):
    """
    gets the stock of a specified item
    :param item_id: the item id whose stock should be returned
    :return: stock of item
    """

@router.post("/{item_id}")
def post_storage(item_id: str):
    """
    posts new stock to a specified item
    :param item_id: the item id in which the new stock should be added
    :return: status of operation
    """
    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement adding stock to an item

@router.patch("/{item_id}")
def patch_storage(item_id: str):
    """
    changes the stock of a specified item
    :param item_id: the item id whose stock should be changed
    :return: status of operation
    """
    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement changing stock of an item

@router.patch("/{item_id}/{amount}")
def add_storage_amount(item_id: str, amount: str):
    """

    :param item_id: the item id whose stock should be added or subtracted
    :param amount: the amount of stock to add or subtract from the current stock (Use - prefix to subtract)
    :return: the new stock of the item
    """

    raise NotImplementedError("Method not implemented yet.")
    # TODO: Implement adding or subtracting stock of an item