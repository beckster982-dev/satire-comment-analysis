Quota Math

Daily Limit Usage: The daily limit for the YouTube Data API v3 is currently 10,000 units. You can only call search. list 100 times a day, but for this project we won't call that; instead, we'll put the chosen videos into a .json file that will use video. list and commentThreads.list to gain information instead, a single unit per call. Each call produces 100 comments, meaning 500 comments can be stored with 5 calls. A video with more than 500 comments will take more than 5 calls because, to reach the first comments, the script will have to skip pages of content to get to content within our desired window. There is also a 200-page limit for comments, but that is beyond the scope of the comments we are working with. Here are three different potential outcomes and how many units each produces. 

Light (comments in video <  500) 
	1 lookup  = 1 unit
	10 videos * 5 Pages = 50 units
	Total = 51 units 

Average (*ASSUMPTION of 60 pages per video to reach first, top-level comments)
	1 lookup - 1 unit
	10 videos * 60 pages  = 600 units
	Total = 601 Units

Heavy 
	1 lookup  = 1 unit
	10 videos * 200 Pages = 2,000 units
	Total = 2,001 units
