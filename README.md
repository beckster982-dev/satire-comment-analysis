# Independent commentary channels comment analysis 
How traditional and independent commentary channels and influencers cover the same event: comment analysis through Youtube. 

Beckett Buchman | November 2026 | Status : Currently setting up 

Research Question - How do independent commentary channels and traditional news channels frame the same event, and how do the sentiment and themes of their YouTube comment sections differ over the fourteen days following it?

Event Focus - IPhone Duo Release (October 23rd - November 6th 2026). test

Channel List - 

IMPORTANT NOTE*- This does not measure public opinion. This data is not an accurate reflection of overall public sentiment; people who choose to go to YouTube and then choose to comment on that particular video are groups who made selective decisions. Instead, this information is meant to describe two separate information environments and their audiences and draw potential relationships. 

What this data can be used to support - The data collected from this analysis can be used to distinguish how each selected channel framed the chosen event and to provide sentiment analysis of their comments over the chosen 14-day window. This information will help illustrate the distribution of analysis over that period and can be used to highlight storylines and themes for each distinct group. 

What this data cannot support - This data does not support whether or not people had their minds changed by the type of information they were watching, or if their opinion was changed at all. As previously mentioned it does not provide general public sentiment and instead highlights two septic forms on information content, traditional and independent commentary channels. It’s not reflective of the speed of the information diffusion or how each channel causal influence.

Sampling Protocol - 
	
Start with a singular event: Clear release date: October 23rd, 00:00 UTC through 14 days after.
Choose up to 10 videos: split them between traditional and independent commentary channels. Videos and channels chosen in the analysis will be listed in both config/events.json and docs/events_and_channels.md. 
Only top-level comments: No replies are included in the analysis. Ordering parameter, order=time is used for each video so that relevance doesn't affect the call, since it switches each time. 
Caps: use 500 top-level replies per video. The script will use a random sample of 500 if more than 500 comments are available. Cap of 5,000 comments for the project.
Identifiers: The comment IDs and video IDs will be saved along with the timestamp of the API call. 
Data storage: Raw data is stored in data/raw/, cleaned data is stored in data/clean/.
Records: Reports are generated after each run, including duplicates, how many comments were in that window, and deleted comments. Deleted comments can't be recalled directly via the APIs, so they would have to be recorded by comparing comment IDs across collections.
Privacy: Comments and authors' names and profiles are never requested or added to a dataset. Data is .gitignore, so the comment data is not accessible in the public repository.
