import json

def make_guess(request):
    game = request.get_json()
    min = game['minimum']
    max = game['maximum']

    for move in game['history']:
        historic_guess = move['guess']
        
        if move['result'] == 'lower':
            if max >= historic_guess:
                max = historic_guess - 1
                
        if move['result'] == 'higher':
            if min <= historic_guess:
                min = historic_guess + 1
                
    guess = (min + max) // 2
    return json.dumps(guess)
