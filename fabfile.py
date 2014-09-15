#!/usr/bin/env python
from collections import defaultdict
import json

from bs4 import BeautifulSoup
from fabric.api import *
import requests

def reset_player_map():
  with open('data/player_map.json', 'w') as writefile:
    writefile.write('{}')

def check_player_map(player_url):
  with open('data/player_map.json', 'r') as readfile:
    player_map = dict(json.loads(readfile.read()))

  if "lastname=" in player_url:
    r = requests.get(player_url)
    soup = BeautifulSoup(r.content)
    search_rows = soup.select('#PlayerSearch1_panSearch table')[1]

    for row in search_rows.select('tr'):
      if "2014" in row.select('td')[2].text:
        player_url = "http://www.fangraphs.com/" + search_rows.select('td')[0].select('a')[0]['href']

  try:
    player = player_map[player_url]

  except (KeyError, ValueError):
    r = requests.get(player_url)
    soup = BeautifulSoup(r.content)

    player_map[player_url] = soup.select('strong')[0].text
    player = player_map[player_url]


  with open('data/player_map.json', 'w') as writefile:
    writefile.write(json.dumps(player_map))

  return player

def scrape_nerd_posts():
  """
  Reads all NERD score posts and writes the results to a JSON file.
  """
  payload = []

  def prepare(index, td):
    """
    Handle the messy logic of preparing each td for processing.
    """
    if index in [0,8]:
      try:
        text = check_player_map(td.select('a')[0]['href'])
      except:
        text = "undecided"

      return unicode(text)

    text = td.text.strip()
    text = unicode(text)

    if ":" in text:
      return text

    try:
      return int(text)

    except ValueError:
      if index in [2, 6]:
        return 0

      return text

  NERD_MAP = ["away_p", "away_t", "away_p_score", "away_t_score", "game_score", "home_t_score", "home_p_score", "home_t", "home_p", "time"]

  r = requests.get('http://www.fangraphs.com/players.aspx?lastname=NERD&type=blog&sort=date')
  link_soup = BeautifulSoup(r.content)
  links = link_soup.select('div.s_stories ul > li > a')

  for link in links:
    if "nerd-game-scores-" in link['href']:
      z = requests.get(link['href'])
      nerd_soup = BeautifulSoup(z.content)
      table = nerd_soup.select('table.sortable')[-1]

      for row in table.select('tr')[1:]:
        payload.append(dict(zip(NERD_MAP, [prepare(i, x) for i, x in enumerate(row.select('td'))])))

  with open('data/scraped_game_scores.json', 'w') as writefile:
    writefile.write(json.dumps(payload))

def calculate_nerd_scores():
  """
  Calculates average NERD scores for each pitcher and team.
  """
  TEAMS = defaultdict(list)
  PITCHERS = defaultdict(list)
  with open('data/scraped_game_scores.json', 'r') as readfile:
    game_scores = list(json.loads(readfile.read()))

  for game_dict in game_scores:
    PITCHERS[game_dict['away_p']].append(game_dict['away_p_score'])
    PITCHERS[game_dict['home_p']].append(game_dict['home_p_score'])

    TEAMS[game_dict['away_t']].append(game_dict['away_t_score'])
    TEAMS[game_dict['home_t']].append(game_dict['home_t_score'])

  PITCHER_SCORES = sorted([{"pitcher": k, "score": float(sum(v))/float(len(v))} for k,v in PITCHERS.items()], key=lambda x:x['score'], reverse=True)
  TEAM_SCORES = sorted([{"team": k, "score": float(sum(v))/float(len(v))} for k,v in TEAMS.items()], key=lambda x:x['score'], reverse=True)

  with open('data/pitcher_scores.json', 'w') as writefile:
    writefile.write(json.dumps(PITCHER_SCORES))

  with open('data/team_scores.json', 'w') as writefile:
    writefile.write(json.dumps(TEAM_SCORES))

def read_nerd_scores():
  with open('data/pitcher_scores.json', 'r') as readfile:
    scores = list(json.loads(readfile.read()))[:25]

  for score in scores:
    print score

  with open('data/team_scores.json', 'r') as readfile:
    scores = list(json.loads(readfile.read()))

  for score in scores:
    print score