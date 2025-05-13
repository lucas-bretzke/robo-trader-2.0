from iqoptionapi.stable_api import IQ_Option
import time
import sys
import getpass

def connect_to_iqoption():
    """Connect to IQ Option platform"""
    print("===== IQ OPTION TRADER =====")
    print("\nLogin to IQ Option")
    
    # Get credentials
    email = input("Email: ")
    senha = getpass.getpass("Password: ")
    
    # Initialize API
    api = IQ_Option(email, senha)
    
    # Connect
    check, reason = api.connect()
    if check:
        print('Connected successfully!')
    else:
        if reason == '{"code":"invalid_credentials","message":"You entered the wrong credentials. Please ensure that your login/password is correct."}':
            print('Incorrect email or password')
        else:
            print('Connection problem:')
            print(reason)
        sys.exit()
    
    return api

def select_account(api):
    """Select demo or real account"""
    while True:
        escolha = input('\nSelect account type (demo/real): ').lower()
        if escolha == 'demo':
            conta = 'PRACTICE'
            print('Demo account selected')
            break
        if escolha == 'real':
            conta = 'REAL'
            print('Real account selected')
            break
        else:
            print('Incorrect choice! Type demo or real')
    
    api.change_balance(conta)
    
    # Display account balance
    balance = api.get_balance()
    print(f'Current balance: {balance}')
    
    return conta

def check_asset_availability(api, asset, tipo):
    """Check if the asset is available for trading"""
    if tipo == 'digital':
        # Check digital option availability
        all_assets = api.get_all_open_time()
        if asset in all_assets['digital']:
            return all_assets['digital'][asset]['open']
        else:
            return False
    else:  # Binary options
        # Check binary option availability
        all_assets = api.get_all_open_time()
        if asset in all_assets['turbo'] or asset in all_assets['binary']:
            return all_assets['turbo'].get(asset, {}).get('open', False) or \
                   all_assets['binary'].get(asset, {}).get('open', False)
        else:
            return False

def get_available_assets(api, tipo):
    """Get list of available assets for trading"""
    all_assets = api.get_all_open_time()
    available_assets = []
    
    if tipo == 'digital':
        for asset in all_assets['digital']:
            if all_assets['digital'][asset]['open']:
                available_assets.append(asset)
    else:  # Binary options
        for asset in all_assets['turbo']:
            if all_assets['turbo'][asset]['open']:
                available_assets.append(asset)
        for asset in all_assets['binary']:
            if all_assets['binary'][asset]['open'] and asset not in available_assets:
                available_assets.append(asset)
                
    return available_assets

def execute_trade(api, ativo, valor, direcao, exp, tipo):
    """Execute a trade and monitor the result"""
    print(f"\nExecuting {direcao.upper()} order on {ativo}")
    print(f"Amount: {valor}, Expiration: {exp}, Type: {tipo}")
    
    # Check if asset is available
    if not check_asset_availability(api, ativo, tipo):
        print(f"Error: {ativo} is currently not available for {tipo} trading.")
        print("The asset might be suspended or closed at this time.")
        return False
    
    # Convert input value to float
    valor = float(valor)
    # Convert expiration to int
    exp = int(exp)
    
    try:
        if tipo == 'digital':
            check, id = api.buy_digital_spot_v2(ativo, valor, direcao, exp)
        else:
            check, id = api.buy(valor, ativo, direcao, exp)

        if check:
            print(f'Order executed with ID: {id}')
            print('Waiting for result...')

            while True:
                time.sleep(0.1)
                status, resultado = api.check_win_digital_v2(id) if tipo == 'digital' else api.check_win_v4(id)

                if status:
                    if resultado > 0:
                        print('WIN', round(resultado, 2))
                    elif resultado == 0:
                        print('DRAW', round(resultado, 2))
                    else:
                        print('LOSS', round(resultado, 2))
                    return True
                    break
        else:
            print(f'Error opening order: {id}')
            return False
    except Exception as e:
        print(f"Trading error: {str(e)}")
        return False

def get_trade_parameters(api):
    """Get trading parameters from user input"""
    print("\n===== TRADE PARAMETERS =====")
    
    # Get trade type first
    while True:
        tipo = input('Trade type (digital/binarias): ').lower()
        if tipo in ['digital', 'binarias']:
            break
        print("Please enter 'digital' or 'binarias'")
    
    # Get available assets
    available_assets = get_available_assets(api, tipo)
    if not available_assets:
        print(f"No assets currently available for {tipo} trading.")
        print("Try a different trade type or try again later.")
        return None, None, None, None, None
    
    print(f"\nAvailable assets ({len(available_assets)}):")
    # Display available assets in groups of 5 per line
    for i in range(0, len(available_assets), 5):
        print(", ".join(available_assets[i:i+5]))
    
    # Get asset
    while True:
        ativo = input('\nAsset to trade (e.g. EURUSD, EURUSD-OTC): ').upper()
        if ativo in available_assets:
            break
        print(f"Asset {ativo} is not available. Please choose from the list above.")
    
    # Get trade amount
    while True:
        try:
            valor = float(input('Trade amount: '))
            break
        except ValueError:
            print("Please enter a valid number")
    
    # Get direction
    while True:
        direcao = input('Direction (call/put): ').lower()
        if direcao in ['call', 'put']:
            break
        print("Please enter 'call' or 'put'")
    
    # Get expiration
    while True:
        try:
            exp = int(input('Expiration time (minutes): '))
            break
        except ValueError:
            print("Please enter a valid number")
    
    return ativo, valor, direcao, exp, tipo

def main():
    """Main function to run the IQ Option trader"""
    try:
        # Connect to IQ Option
        api = connect_to_iqoption()
        
        # Select account type
        select_account(api)
        
        while True:
            # Get trade parameters
            ativo, valor, direcao, exp, tipo = get_trade_parameters(api)
            
            # Check if we got valid parameters
            if ativo is None:
                print("Failed to get trading parameters.")
                if input("\nTry again? (y/n): ").lower() != 'y':
                    break
                continue
            
            # Execute trade
            execute_trade(api, ativo, valor, direcao, exp, tipo)
            
            # Ask if user wants to make another trade
            another = input("\nMake another trade? (y/n): ").lower()
            if another != 'y':
                break
        
        print("\nThank you for using IQ Option Trader!")
        
    except KeyboardInterrupt:
        print("\n\nTrading session interrupted.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
