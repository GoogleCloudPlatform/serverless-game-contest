import json

def make_guess(request):
    game = request.get_json()
    guess = game['minimum']

    for move in game['history']:
        historic_guess = move['guess']
        
        if move['result'] == 'lower':
            if guess >= historic_guess:
                guess = historic_guess - 1
                
        if move['result'] == 'higher':
            if guess <= historic_guess:
                guess = historic_guess + 1
                
    return json.dumps(guess)
