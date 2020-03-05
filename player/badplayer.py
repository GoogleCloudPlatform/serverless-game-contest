import json

def make_guess(request):
    game = request.get_json()
    guess = game['minimum']
    return json.dumps(guess)
