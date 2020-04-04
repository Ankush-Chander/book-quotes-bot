import os
import sys, getopt
import tweepy
import aiohttp
import asyncio
from bs4 import BeautifulSoup

# Plan of action
# 1. Whenever I start reading any book. Inform script
# 2. crawl all quotes of that book(done)
# 3. Tweet quotes daily


current_dir = os.path.dirname(os.path.realpath(__file__))


def add_to_sys_path(new_path):
	sys.path.append(f"{current_dir}/{new_path}")


add_to_sys_path("../utility")
from config_var import consumer_key, consumer_secret, access_token, access_token_secret


async def fetch(session, url):
	async with session.get(url) as response:
		return await response.text()


async def fetch_quotes_from_url(session, url):
	html_doc = await fetch(session, url)
	soup = BeautifulSoup(html_doc, 'html.parser')
	quote_divs = soup.find_all("div", class_="quoteText")
	next_page = soup.find("a", class_="next_page")
	if next_page:
		last_page = next_page.find_previous_sibling("a")
		# print(f"last_page:{last_page}")
		total_pages = last_page.get_text()
		# print(total_pages)
		assert total_pages.isdigit()
		total_pages = int(total_pages)
	else:
		total_pages = None
	quotes = [div.contents[0].strip() for div in quote_divs]

	return total_pages, quotes


async def get_quotes_by_book(url):
	quotes = []
	total_pages = None
	async with aiohttp.ClientSession() as session:
		total_pages, page_quotes = await fetch_quotes_from_url(session, url)
		quotes = quotes + page_quotes
		for i in range(2, total_pages + 1):
			page_url = f"{url}?page={i}"
			total_pages, page_quotes = await fetch_quotes_from_url(session, page_url)
			quotes = quotes + page_quotes
		return quotes


async def update_status(text):
	assert len(text) < 240
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)
	api = tweepy.API(auth)
	x = api.update_status(text)


async def save_book_quotes(url, name):
	quotes = await get_quotes_by_book(url)
	await write_book_quotes(quotes, name)


async def write_book_quotes(quotes, name):
	with open(f"../quotes/{name}.json", "w+") as fp:
		fp.write(str(quotes))
		print(f"Added {len(quotes)} quotes to {name}")


def get_latest_file(path):
	"""Returns the name of the latest (most recent) file
	of the joined path(s)"""
	# TODO: remove hardcode ad pick up latest crawled quotes
	filename = "../quotes/courage_to_be_disliked.json"
	return filename


async def daily_tweet():
	filename = get_latest_file("../quotes")
	with open(filename, "r") as fp:
		quotes = eval(fp.read())
		assert isinstance(quotes, list)
	# print(quotes)
	for quote in quotes:
		if len(quote) < 240:
			await update_status(quote)
			break
	# 	tweet quote
	shifted_quotes = quotes[1:] + quotes[:1]
	assert len(shifted_quotes) == len(quotes)
	with open(filename, "w") as fp:
		fp.write(str(shifted_quotes))


if __name__ == '__main__':
	short_options = "h:u:n:t"
	long_options = ["help", "url=", "name=", "tweet"]
	myopts, args = getopt.getopt(sys.argv[1:], short_options, long_options)
	book_quote_url = None
	book_name = None

	# TODO: make control flow more robust
	# TODO: add help script
	for option, a in myopts:
		if option == "--tweet":
			loop = asyncio.get_event_loop()
			loop.run_until_complete(daily_tweet())
		elif option == "--url":
			print(f"url:{a}")
			book_quote_url = a
		elif option == "--name":
			print(f"name:{a}")
			book_name = a

	if book_name and book_quote_url:
		print(f"crawling:{book_quote_url} for book:{book_name}")
		loop = asyncio.get_event_loop()
		loop.run_until_complete(save_book_quotes(book_quote_url, book_name))
