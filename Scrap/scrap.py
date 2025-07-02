from urllib.request import urlopen
from json import dumps
from time import sleep

def safeClean(text,begin,end,startAt):
  phraseB = text.find(begin,startAt)
  if phraseB == -1:
    return None
  phraseE = text.find(end,phraseB+len(begin))
  if phraseE == -1:
    return None
  else:
    return text[phraseB+len(begin):phraseE]

def bolToJSON(b):
  if b:
    return "true"
  else:
    return "false"

class PlayerSurveyResult:
  def __init__(self,count,good,okay,andAbove):
    self.count = count
    self.good=good
    self.okay=okay
    self.andAbove = andAbove
  
  def toJSON(self):
    return dumps(self.__dict__)
  
  
  def __str__(self):
    return str(self.count)+("+: " if self.andAbove else ": ") + "[good: " + self.good + ", okay: "+self.okay +"]"
  
  def __repr__(self):
    return str(self)

class BoardGame:
  def __init__(self,inid):
    self.url = "https://boardgamegeek.com/boardgame/" + str(inid)
    self.id = int(inid)
    self.complexity = -1
    self.nPC = -1
    self.nWeights = -1
    self.raters = -1
    self.recommendedPC = None
    self.rating = -1
    self.title = None
    self.minPC = -1
    self.maxPC = -1
    self.minTime = -1
    self.maxTime = -1
    self.genre = []
    print("Stage 0")

    if id!=-1:
      #Aquire BG information from board game geek
      qRes = urlopen("https://boardgamegeek.com/xmlapi2/thing?id="+str(self.id)+"&stats=1").read().decode("utf-8")

      #Gets BG title
      titleStart = qRes.find("<name type=\"primary\"")
      if titleStart != -1:
        self.title = safeClean(qRes, "value=\"","\"",titleStart)

      #Gets BG rating and number of users who rated
      statIndex = qRes.find("<statistics page=\"1\">")
      ratersSTR = safeClean(qRes,"<usersrated value=\"", "\"",statIndex)
      try:
        self.raters = int(ratersSTR)
      except:
        print("invalid number of raters for BG: " + self.url + "\n raters: "+ ratersSTR)

      if (self.raters >= 20):
        ratingSTR = safeClean(qRes,"<average value=\"","\"",statIndex)
        try:
          self.rating = round(float(ratingSTR),3)
        except:
          print("invaild rating for BG: " + self.url + "\n rating: " + ratingSTR)
      
      #Gets complexity and number of users who rated
      nWeightSTR = safeClean(qRes, "<numweights value=\"", "\"",statIndex)
      try:
        self.nWeights = int(nWeightSTR)
      except:
        print("invaild number of complexity ratings for BG: " + self.url + "\n number: " + complexitySTR)
      if (True):
        complexitySTR = safeClean(qRes, "<averageweight value=\"", "\"", statIndex)
        try:
          self.complexity = round(float(complexitySTR),3)
        except:
          print("invaild complexity for BG: " + self.url + "\n complexity: " + complexitySTR)
      

      #Manufacurers Player Count
      minPCS = safeClean(qRes,"<minplayers value=\"","\"",0)
      maxPCS = safeClean(qRes,"<maxplayers value=\"","\"",0)
      try:
        self.minPC = int(minPCS)
        self.maxPC = int(maxPCS)
      except:
        print("Unable to convert max/min players for BG: " + self.id + "\n Max: " + maxPCS+ "\n Min: " + minPCS)

      #Gets submitted ideal player count
      pcPoll = safeClean(qRes,"<poll name=\"suggested_numplayers\"","</poll>",0)
      nPCSTR = safeClean(pcPoll, "totalvotes=\"","\"",0)
      try:
        self.nPC = int(nPCSTR)
      except:
        print("Unable to determine number of player count voters for BG url: " + self.url+ "\n number: "+ nPCSTR)
      if (True):
        current = pcPoll.find("<results numplayers=\"")
        self.recommendedPC = []
        while (pcPoll.find("<results numplayers=\"",current)>=0):
          nPlayerSTR = safeClean(pcPoll,"<results numplayers=\"","\"",current)
          andAbove = False
          nPlayer = 0
          try:
            nPlayer = int(nPlayerSTR)
          except:
            try:
              nPlayer = int(nPlayerSTR[:-1])
              andAbove = True
            except:
              print("couldn't read" + nPlayerSTR +" as int for BG url: " + self.url)
          try:
            res = (0,0,0)
            if(self.nPC > 0):
              res = (int(safeClean(pcPoll,"<result value=\"Best\" numvotes=\"","\"",current))/self.nPC,
                  int(safeClean(pcPoll,"<result value=\"Recommended\" numvotes=\"","\"",current))/self.nPC,
                  int(safeClean(pcPoll,"<result value=\"Not Recommended\" numvotes=\"","\"",current))/self.nPC)
            #psrSTR = "{\"nPlayers\":"+str(nPlayer) +", \"andAbove\":" +bolToJSON(andAbove)+", \"good\":" + str(res[0])+", \"okay\":" + str(res[1])+", \"bad\":" + str(res[2])+"}"
            psr = PlayerSurveyResult(nPlayer,round(res[0],3),round(res[1]+res[0],3),andAbove)
            self.recommendedPC.append(psr)
          except:
            print("couldn't read player count survery results for " + nPlayerSTR+ "for BG url: " + self.url)
          current = pcPoll.find("<results numplayers=\"",current+1)
      
      #Time information
      minTimeString = safeClean(qRes,"<minplaytime value=\"","\"",0)
      maxTimeString = safeClean(qRes,"<maxplaytime value=\"","\"",0)
      try:
        self.minTime = int(minTimeString)
        self.maxTime = int(maxTimeString)
      except:
        print("unable to determine min or max playtime for BG: " + self.url+"\nMin: " + minTimeString+"\nMax: " + maxTimeString)
      
      try:
        self.genre = extractGenre(self.id)
      except:
        print("Unable to extract genre for BG: " + str(self.id))
        



  
  def __str__(self):
    #return dumps(self.__dict__,sort_keys=True, indent=2)
    return dumps(self.__dict__,default=vars,sort_keys=True, indent=2)

def extractGenre(id):
  try:
    results = []
    sleep(5)
    print("Stage 1")
    pollid = int(safeClean(urlopen("https://boardgamegeek.com/geekitempoll.php?action=view&itempolltype=boardgamesubdomain&objectid="+str(id)+"&objecttype=thing").read().decode("utf-8"),"<div id=\"pollquestions","\"",0))
    sleep(5)
    print("Stage 2")
    stage2 = urlopen("https://boardgamegeek.com/geekpoll.php?action=results&pollid="+str(pollid)).read().decode("utf-8")
    tv = int(safeClean(stage2,"<td class=\"answered\">","</td>",0))
    print("Total Votes: " + str(tv))
    #print(stage2)
    searchIndex = 0
    if (tv >= 5):
      for genre in ["Abstract Strategy", "Customizable", "Thematic", "Family", "Children", "Party", "Strategy", "Wargames"]:
        k = stage2.find("<td class=\"votes\">",searchIndex)
        searchIndex = stage2.find("</td>",k)
        votes = int(stage2[k+len("<td class=\"votes\">"):searchIndex].strip())
        if ((votes/tv)>0.3):
          results.append(genre)
    return results
  except:
    print ("Unable to find genre poll id for BG: " + str(id))


inu = open("BGids.csv","r", encoding="utf-8-sig")
out = open("BGdata.json","w")
out.write("[")
out.close()
urls = inu.read().split("\n")
seen = []
inu.close()
for i in range(0,len(urls)):
  out2 = open("BGdata.json","a")
  looked = False
  try:
    print("Started board game "+ str(i+1) + " of " + str(len(urls)))
    if (int(urls[i].strip()) not in seen):
      looked = True
      seen.append(int(urls[i]))
      tempBG = BoardGame(urls[i].strip())
      if (len(seen) == 1):
        out2.write(str(tempBG))
        print("Completed first BG of " + str(len(urls)))
      else:
        out2.write(","+str(tempBG))
        print("Completed board game "+ str(i+1) + " of " + str(len(urls)))
    else:
      print("Skipped BG " + str(i+1) + " of " + str(len(urls)) + ", duplicate")
  except:
    print("Failed board game " + str(i+1) + " of " + str(len(urls)) + ". URL: " + urls[i])
  out2.close()

  if (i != len(urls) -1) and looked:
    sleep(5)
out = open("BGdata.json","a")
out.write("]")
out.close()
#print(BoardGame(21804))



#print(extractGenre(160452))
#print(urlopen("https://boardgamegeek.com/geekitempoll.php?action=view&itempolltype=boardgamesubdomain&objectid=237182&objecttype=thing").read().decode("utf-8"))