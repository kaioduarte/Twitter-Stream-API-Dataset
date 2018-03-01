from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from pymongo import MongoClient
import pymongo
import json
from flask import Flask, jsonify, request
import time
from datetime import datetime
from bson import json_util



#---------------MONGODB--------------------

client = MongoClient()
db = client.test
#db.tweets.remove()
tweets = db.tweets

#------------------TWIITTER---DETAILS--------------

access_token = "777222101556076544-Bji7W4PDJUetIYQUMvAwAfDse2n8STq"
access_token_secret = "gxJNRMTF4xFuwt95uzw4g2bEQFs19tyJmsepdLjSCo1C3"
consumer_key ="5x5j9zymoR9AMLbWSocviZ32J"
consumer_secret = "HPPrlY2pLFxJjJ5zbxbjP9leH1fhyxE312Wa4NO80XZQX8gJ73"

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)


#----------------FLASK---ENDPOINTS-------------------

app = Flask(__name__)


@app.route('/',methods=['GET'])
def hello():
	return jsonify({'hello':'world'})

#-------------TRIGGER------------------------

@app.route('/triggertweets',methods=['GET'])
def triggertweets():
	key = request.args['keyword']
	if key==None:
		return ('No keyword Present')
	max_tweets = int(request.args.get('max_tweets',10))

	#print(key)
	l = StdOutListener(key,max_tweets)
	stream = Stream(auth, l)
	stream.filter(track=[key], async=True)
	return jsonify({"trigger":"started"})

#--------------Return Tweets--------------------

@app.route('/gettweets', methods=['GET'])
def getTweets():
	key = request.args['keyword']
	offset = int(request.args.get('offset',0))
	limit = int(request.args.get('limit',10))
	
	name = request.args.get('name',None)
	screenname = request.args.get('screen_name',None)
	retweet_count = int(request.args.get('retweet_count',-1))
	reply_count = int(request.args.get('reply_count',-1))
	favorite_count = int(request.args.get('favorite_count',-1))
	language = request.args.get('lang',None)

	filters = {'keyword':key}

	next_url = '/gettweets?keyword=' + str(key)
	prev_url = '/gettweets?keyword=' + str(key)


	if name!=None:
		filters['name'] = name
		next_url += '&name='+name
		prev_url += '&name='+name
	if screenname!=None:
		filters['screen_name'] = screenname
		next_url += '&screen_name='+screenname
		prev_url += '&screen_name='+screenname
	if retweet_count!=-1:
		filters['retweet_count'] = retweet_count
		next_url += '&retweet_count=' + str(retweet_count)
		prev_url += '&retweet_count=' + str(retweet_count)
	if reply_count!=-1:
		filters['reply_count'] = reply_count
		next_url += '&reply_count=' + str(reply_count)
		prev_url += '&reply_count=' + str(reply_count)
	if favorite_count!=-1:
		filters['favorite_count'] = favorite_count
		next_url += '&favorite_count=' + str(favorite_count)
		prev_url += '&favorite_count=' + str(favorite_count)
	if language!=None:
		filters['lang'] = language
		next_url += '&lang=' + language
		prev_url += '&lang=' + language
	
	sort_by = request.args.get('sort_by',None)
	order_by = request.args.get('order','ASC');
	if sort_by==None:
		sort_by = '_id'
		next_url += '&sort_by=' + sort_by
		prev_url += '&sort_by=' + sort_by
	else:
		next_url += '&sort_by=' + sort_by
		prev_url += '&sort_by=' + sort_by
	
	order = 0
	if(order_by=='ASC'):
		order = 0
		next_url += '&order=' + order_by
		prev_url += '&order=' + order_by
	else:
		order = 1
		next_url += '&order=' + order_by
		prev_url += '&order=' + order_by


	next_url += '&limit=' + str(limit) + '&offset=' + str(offset+limit)
	prev_url += '&limit=' + str(limit) + '&offset=' + str(offset-limit)


	if order==0:
		query = tweets.find(filters).sort(sort_by,pymongo.ASCENDING)
	else:
		query = tweets.find(filters).sort(sort_by,pymongo.DESCENDING)

	
	starting_id = query
	try:
		last_id = starting_id[offset]['_id']
	except:
		last_id= 0


	if order==0:
		filters['_id'] = {'$gte':last_id}
	else:
		filters['_id'] = {'$lte':last_id}
	
	s = []
	
	try:
		count = 0;
		full_find = query
		for tweet in full_find:
			#print(tweet)
			s.append(tweet)
			count += 1
			if count==limit:
				break
	except:
		s = []
	ans = {}
	ans['tweet_count'] = len(s)
	ans['limit'] = limit
	ans['offset'] = offset
	if offset+limit<=len(s):
		ans['next_url'] = next_url
	if offset-limit>=0:
		ans['prev_url'] = prev_url
	ans['tweets'] = json_util._json_convert(s)
	return jsonify(ans)

#----------------TWEEPY STREAM LISTENER----------------------------


class StdOutListener(StreamListener):
	
	count = 0
	keyword = ""
	max_tweets = 0

	def __init__(self,key, max_tweets):
		self.max_tweets = max_tweets
		self.count = 0
		self.keyword += key

	def on_data(self,data):

		obj = json.loads(data)
		
		tweet = {}
		tweet['keyword'] = self.keyword

		tweet['text'] = obj['text']
		tweet['lang'] = obj['user']['lang']
		tweet['timestamp_ms'] = obj['timestamp_ms']
		tweet['retweeted'] = obj['retweeted']
		tweet['retweet_count'] = obj['retweet_count']
		tweet['reply_count'] = obj['reply_count']
		tweet['favorite_count'] = obj['favorite_count']

		

		#print(tweet['created_at'])

		hashes = obj['entities']['hashtags']
		hashtags = []
		for hashtag in hashes:
			hashtags.append(hashtag['text'])
		tweet['tweet_hashtags'] = hashtags

		urls_list = obj['entities']['urls']
		urls = []
		for url in urls_list:
			urls.append(url['url'])
		tweets['tweet_text_urls']


		tweet['user_id'] = obj['user']['id']
		tweet['name'] = obj['user']['name']
		tweet['screen_name'] = obj['user']['screen_name']
		tweet['location'] = obj['user']['location']
		tweet['url'] = obj['user']['url']
		tweet['user_description'] = obj['user']['description']
		tweet['user_followers_count'] = obj['user']['followers_count']
		tweet['user_friends_count'] = obj['user']['friends_count']
		tweet['user_time_zone'] = obj['user']['time_zone']

		time_struct = time.strptime(obj['created_at'], "%a %b %d %H:%M:%S +0000 %Y")#Tue Apr 26 08:57:55 +0000 2011
		tweet['created_at'] = datetime.fromtimestamp(time.mktime(time_struct))

		#print(tweet)

		tweets.insert_one(tweet)
		print("Success")
		self.count += 1
		if self.count == self.max_tweets:
			del self
			return False
		return True

	def on_error(self,status):
		print("Failed - Error: ",status)



if __name__ == '__main__':
	app.run(port=5000,use_reloader=True)