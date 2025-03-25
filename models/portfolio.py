import uuid
from datetime import datetime

class Portfolio:
    """Model for user portfolios"""
    
    # In-memory storage for portfolios
    portfolios = {}
    
    def __init__(self, user_id, name="Default Portfolio"):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.name = name
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.holdings = []  # List of portfolio holdings
        self.total_invested = 0.0
        self.current_value = 0.0
        
        # Save to in-memory storage
        if user_id not in Portfolio.portfolios:
            Portfolio.portfolios[user_id] = []
        Portfolio.portfolios[user_id].append(self)
    
    @staticmethod
    def get_user_portfolios(user_id):
        """Get all portfolios for a user"""
        return Portfolio.portfolios.get(user_id, [])
    
    @staticmethod
    def get_portfolio(portfolio_id):
        """Get a specific portfolio by ID"""
        for user_portfolios in Portfolio.portfolios.values():
            for portfolio in user_portfolios:
                if portfolio.id == portfolio_id:
                    return portfolio
        return None
    
    def add_holding(self, symbol, amount, price_per_unit, date=None):
        """Add a cryptocurrency holding to the portfolio"""
        if date is None:
            date = datetime.now()
            
        holding = {
            'id': str(uuid.uuid4()),
            'symbol': symbol,
            'amount': float(amount),
            'price_per_unit': float(price_per_unit),
            'date_acquired': date,
            'current_price': float(price_per_unit),  # Will be updated
            'current_value': float(amount) * float(price_per_unit),
            'profit_loss': 0.0  # Will be calculated
        }
        
        self.holdings.append(holding)
        self.total_invested += holding['amount'] * holding['price_per_unit']
        self.current_value += holding['current_value']
        self.updated_at = datetime.now()
        
        return holding
    
    def update_holding(self, holding_id, amount=None, price_per_unit=None):
        """Update an existing holding"""
        for holding in self.holdings:
            if holding['id'] == holding_id:
                old_invested = holding['amount'] * holding['price_per_unit']
                old_value = holding['current_value']
                
                if amount is not None:
                    holding['amount'] = float(amount)
                
                if price_per_unit is not None:
                    holding['price_per_unit'] = float(price_per_unit)
                
                # Recalculate values
                new_invested = holding['amount'] * holding['price_per_unit']
                holding['current_value'] = holding['amount'] * holding['current_price']
                
                # Update portfolio totals
                self.total_invested = self.total_invested - old_invested + new_invested
                self.current_value = self.current_value - old_value + holding['current_value']
                self.updated_at = datetime.now()
                
                return holding
        
        return None
    
    def remove_holding(self, holding_id):
        """Remove a holding from the portfolio"""
        for i, holding in enumerate(self.holdings):
            if holding['id'] == holding_id:
                # Update portfolio totals
                self.total_invested -= holding['amount'] * holding['price_per_unit']
                self.current_value -= holding['current_value']
                self.updated_at = datetime.now()
                
                # Remove the holding
                return self.holdings.pop(i)
        
        return None
    
    def update_prices(self, price_data):
        """Update current prices of all holdings"""
        for holding in self.holdings:
            symbol = holding['symbol']
            if symbol in price_data:
                old_value = holding['current_value']
                holding['current_price'] = float(price_data[symbol])
                holding['current_value'] = holding['amount'] * holding['current_price']
                holding['profit_loss'] = holding['current_value'] - (holding['amount'] * holding['price_per_unit'])
                
                # Update portfolio total value
                self.current_value = self.current_value - old_value + holding['current_value']
        
        self.updated_at = datetime.now()
        
        return self.holdings
    
    def calculate_performance(self):
        """Calculate portfolio performance metrics"""
        total_invested = self.total_invested
        current_value = self.current_value
        
        if total_invested == 0:
            return {
                'total_invested': 0,
                'current_value': 0,
                'profit_loss': 0,
                'profit_loss_percent': 0,
                'holdings_count': len(self.holdings)
            }
        
        profit_loss = current_value - total_invested
        profit_loss_percent = (profit_loss / total_invested) * 100
        
        return {
            'total_invested': total_invested,
            'current_value': current_value,
            'profit_loss': profit_loss,
            'profit_loss_percent': profit_loss_percent,
            'holdings_count': len(self.holdings)
        }
