import json
import boto3
import random
import math

class IdSentence:
    """Generate human-readable IDs composed of adjectives, nouns, and verbs."""

    def __init__(self):
        self.adjectives = [
            'adorable', 'adventurous', 'alluring', 'amazing',
            'ambitious', 'amusing', 'astonishing', 'attractive', 'awesome',
            'bashful', 'bawdy', 'beautiful', 'bewildered', 'bizarre', 'bouncy',
            'brainy', 'brave', 'brawny', 'burly', 'capricious', 'careful',
            'caring', 'cautious', 'charming', 'cheerful', 'chivalrous',
            'classy', 'clever', 'clumsy', 'colossal', 'cool', 'coordinated',
            'courageous', 'cuddly', 'curious', 'cute', 'daffy', 'dapper',
            'dashing', 'dazzling', 'delicate', 'delightful', 'determined',
            'eager', 'embarrassed', 'enchanted', 'energetic', 'enormous',
            'entertaining', 'enthralling', 'enthusiastic', 'evanescent',
            'excited', 'exotic', 'exuberant', 'exultant', 'fabulous', 'fancy',
            'festive', 'finicky', 'flashy', 'flippant', 'fluffy', 'fluttering',
            'funny', 'furry', 'fuzzy', 'gaudy', 'gentle', 'giddy', 'glamorous',
            'gleaming', 'goofy', 'gorgeous', 'graceful', 'grandiose', 'groovy',
            'handsome', 'happy', 'hilarious', 'honorable', 'hulking',
            'humorous', 'industrious', 'incredible', 'intelligent', 'jazzy',
            'jolly', 'joyous', 'kind', 'macho', 'magnificent', 'majestic',
            'marvelous', 'mighty', 'mysterious', 'naughty', 'nimble', 'nutty',
            'oafish', 'obnoxious', 'outrageous', 'pretty', 'psychedelic',
            'psychotic', 'puzzled', 'quirky', 'quizzical', 'rambunctious',
            'remarkable', 'sassy', 'shaggy', 'smelly', 'sneaky', 'spiffy',
            'swanky', 'sweet', 'swift', 'talented', 'thundering', 'unkempt',
            'upbeat', 'uppity', 'wacky', 'waggish', 'whimsical', 'wiggly',
            'zany'
        ]

        self.nouns = [
            'aardvarks', 'alligators', 'alpacas', 'anteaters', 'antelopes',
            'armadillos', 'baboons', 'badgers', 'bears', 'beavers',
            'boars', 'buffalos', 'bulls', 'bunnies', 'camels', 'cats',
            'chameleons', 'cheetahs', 'centaurs', 'chickens', 'chimpanzees',
            'chinchillas', 'chipmunks', 'cougars', 'cows', 'coyotes', 'cranes',
            'crickets', 'crocodiles', 'deers', 'dinasaurs', 'dingos', 'dogs',
            'donkeys', 'dragons', 'elephants', 'elves', 'ferrets', 'flamingos',
            'foxes', 'frogs', 'gazelles', 'giraffes', 'gnomes', 'gnus', 'goats',
            'gophers', 'gorillas', 'hamsters', 'hedgehogs', 'hippopotamus',
            'hobbits', 'hogs', 'horses', 'hyenas', 'ibexes', 'iguanas',
            'impalas', 'jackals', 'jackalopes', 'jaguars', 'kangaroos',
            'kittens', 'koalas', 'lambs', 'lemmings', 'leopards', 'lions',
            'ligers', 'lizards', 'llamas', 'lynxes', 'meerkat', 'moles',
            'mongooses', 'monkeys', 'moose', 'mules', 'newts', 'okapis',
            'orangutans', 'ostriches', 'otters', 'oxes', 'pandas', 'panthers',
            'peacocks', 'pegasuses', 'phoenixes', 'pigeons', 'pigs',
            'platypuses', 'ponies', 'porcupines', 'porpoises', 'pumas',
            'pythons', 'rabbits', 'raccoons', 'rams', 'reindeers',
            'rhinoceroses', 'salamanders', 'seals', 'sheep', 'skunks',
            'sloths', 'slugs', 'snails', 'snakes', 'sphinxes', 'sprites',
            'squirrels', 'takins', 'tigers', 'toads', 'trolls', 'turtles',
            'unicorns', 'walruses', 'warthogs', 'weasels', 'wolves',
            'wolverines', 'wombats', 'woodchucks', 'yaks', 'zebras'
        ]

        self.verbs = [
            'ambled', 'assembled', 'burst', 'babbled', 'charged', 'chewed',
            'clamored', 'coasted', 'crawled', 'crept', 'danced', 'dashed',
            'drove', 'flopped', 'galloped', 'gathered', 'glided', 'hobbled',
            'hopped', 'hurried', 'hustled', 'jogged', 'juggled', 'jumped',
            'laughed', 'marched', 'meandered', 'munched', 'passed', 'plodded',
            'pranced', 'ran', 'raced', 'rushed', 'sailed', 'sang', 'sauntered',
            'scampered', 'scurried', 'skipped', 'slogged', 'slurped', 'spied',
            'sprinted', 'spurted', 'squiggled', 'squirmed', 'stretched',
            'strode', 'strut', 'swam', 'swung', 'traveled', 'trudged',
            'tumbled', 'twisted', 'wade', 'wandered', 'whistled', 'wiggled',
            'wobbled', 'yawned', 'zipped', 'zoomed'
        ]

def lambda_handler(event, context):
    try:
        quiz_data = json.loads(event['body'])
        title = quiz_data['Title']
        questions = quiz_data['Questions']
        visibility = quiz_data.get('Visibility', 'Private')
        if visibility not in ('Public', 'Private'):
            raise ValueError("Visibility must be 'Public' or 'Private'")
    except (KeyError, json.JSONDecodeError, ValueError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid input data',
                'error': str(e)
            })
        }

    for question in questions:
        if not all(k in question for k in ('QuestionText', 'Options', 'CorrectAnswer', 'Trivia')):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Each question must contain QuestionText, Options, CorrectAnswer, and Trivia'
                })
            }

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Quizzes')
    id_sentence = IdSentence()

    max_attempts = 5
    attempt = 0
    quiz_id = None

    while attempt < max_attempts:
        adjective = random.choice(id_sentence.adjectives)
        noun = random.choice(id_sentence.nouns)
        verb = random.choice(id_sentence.verbs)
        quiz_id = f"{adjective}-{noun}-{verb}"

        existing_quiz = table.get_item(Key={'QuizID': quiz_id})
        if 'Item' not in existing_quiz:
            break
        attempt += 1
        quiz_id = None

    if not quiz_id:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Failed to generate a unique QuizID. Please try again.'})
        }

    quiz_data['QuizID'] = quiz_id
    quiz_data['Visibility'] = visibility
    try:
        table.put_item(Item=quiz_data)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error storing quiz data', 'error': str(e)})
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'QuizID': quiz_id})
    }
