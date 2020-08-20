from flask import render_template, jsonify, Response, request, url_for
from app import app, mongo
from app.tasks import send_web_push, add_notification_to_db, publish
import requests
from datetime import datetime

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/v1/vapid/public/key')
def get_vapid_public_key():
    pub_key = app.config['VAPID_PUBLIC_KEY']
    if pub_key is None:
        return Response(status=404)

    return jsonify({'public_key': pub_key})


@app.route('/api/v1/subscribers/', methods=["POST"])
def post_subscription_token():
    if not request.json or not request.json.get('sub_token') or not request.json.get('industry'):
        return Response(status=400)

    collection = mongo.db.industries
    industry = request.json.get('industry')
    sub_token = request.json.get('sub_token')
    if collection.find_one({'industry': industry}):
        collection.update_one({'industry': industry}, {'$addToSet': {'sub_token': sub_token}})
    else:
        collection.insert_one({'industry': industry, 'subtoken': [sub_token], 'notifications': []})

        # TODO: Start monitoring the added industry in the database

    return Response(status=201)


@app.route('/api/v1/subscribers/list')
def list_subscribers():
    timestamp = request.args.get("timestamp")

    collection = mongo.db.industries
    res = list(collection.find({}, {'_id': 0}))
    # TODO: Retrieve notifications based on timestamp
    return jsonify(res)


@app.route('/api/v1/notifications/push', methods=["POST"])
def push_notifications():
    if not request.json or not request.json.get('industry') or not request.json.get('notification'):
        return Response(status=400)
    
    industry = request.json.get('industry')
    notification = request.json.get('notification')

    collection = mongo.db.industries
    industry_document = collection.find_one({'industry': industry})
    if not industry_document:
        return Response(status=400)

    tokens = industry_document['subtoken']

    for token in tokens:
        send_web_push.queue(token, notification)
    
    # TODO: Send notifications to mobile phones
    notification['timestamp'] = datetime.utcnow()
    add_notification_to_db.queue(industry, notification)
    
    return Response(status=200)


@app.route('/api/v1/notifications/list')
def list_notifications_of_industry():
    if not request.args.get('industry'):
        return Response(status=400)
    
    industry = request.args.get('industry')
    collection = mongo.db.industries
    res = collection.find_one({'industry': industry}, {'notifications': 1, '_id': 0})
    if res is None:
        return Response(status=400)

    return jsonify(res['notifications'])


@app.route('/api/v1/topics/', methods=["POST"])
def create_topic():
    if not request.json or not request.json.get('topic'):
        return Response(status=400)

    topic_name = request.json.get('topic')
    description = request.json.get('description')
    if description is None:
        description = ""

    collection = mongo.db.topics
    if collection.find_one({'topic': topic_name}):
        return Response(status=400)
    
    collection.insert_one({'topic': topic_name, 'description': description, 'industries': []})
    return Response(status=201)


@app.route('/api/v1/topics/list')
def list_topics():
    collection = mongo.db.topics
    res = list(collection.find({}, {'_id': 0}))
    return jsonify(res)


@app.route('/api/v1/topics/subscriber', methods=["PUT"])
def subscribe_industry_to_topic():
    if not request.json or not request.json.get('topic') or not request.json.get('industry'):
        return Response(status=400)
    
    topic_name = request.json.get('topic')
    industry = request.json.get('industry')

    topics_collection = mongo.db.topics
    indistry_collection = mongo.db.industries

    if not indistry_collection.find_one({'industry': industry}):
        return Response(status=400)

    res = topics_collection.update_one({'topic': topic_name}, {'$addToSet': {'industries': industry}})
    if res.raw_result['n'] == 0:
        return Response(status=400)

    return Response(status=200)


@app.route('/api/v1/topics/publish', methods=["POST"])
def publish_message_to_a_topic():
    if not request.json or not request.json.get('notification') or not request.json.get('topic'):
        return Response(status=400)

    topic_name = request.json.get('topic')
    notification = request.json.get('notification')

    collection = mongo.db.topics

    topic_document = collection.find_one({'topic': topic_name})
    if not topic_document:
        return Response(status=400)
    
    industries = topic_document['industries']
    publish.queue(industries, notification)
    
    return Response(status=200)


@app.route('/api/v1/topics/unsubscribe', methods=["POST"])
def unsubscribe_industry_from_topic():
    if not request.json or not request.json.get('industry') or not request.json.get('topic'):
        return Response(status=400)
    
    industry = request.json.get('industry')
    topic_name = request.json.get('topic')

    collection = mongo.db.topics
    
    res = collection.update_one({'topic': topic_name}, {'$pull': {'industries': industry}})
    if res.raw_result['n'] == 0 or res.raw_result['nModified'] == 0:
        return Response(status=400)

    return Response(status=200)


@app.route('/api/v1/topics/<topic>', methods=["DELETE"])
def remove_topic(topic):
    collection = mongo.db.topics

    res = collection.remove({'topic': topic})
    if res['n'] == 0:
        return Response(status=400)
    
    return Response(status=200)
    