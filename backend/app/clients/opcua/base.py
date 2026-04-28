class ProductionClient:
    def get_status(self) -> str:
        raise NotImplementedError
    
    def post_order(self, order):
        raise NotImplementedError
    
    def get_order_status(self, order_id):
        raise NotImplementedError
    
    